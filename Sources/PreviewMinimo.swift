import Cocoa
import SwiftUI

struct Job: Identifiable {
    let id = UUID()
    let url: URL
    var state = "Na fila"
    var progress = 0.0
    var output: String? = nil
    var error: String? = nil
}

final class QueueModel: ObservableObject {
    @Published var jobs: [Job] = []
    @Published var running = false
    @Published var stopping = false
    private var process: Process?
    private var activeID: UUID?
    var totalProgress: Double { jobs.isEmpty ? 0 : jobs.reduce(0) { $0 + ($1.state == "Concluído" || $1.state == "Erro" || $1.state == "Cancelado" ? 1 : $1.progress) } / Double(jobs.count) }
    var completed: Int { jobs.filter { $0.state == "Concluído" }.count }

    func add(_ urls: [URL]) {
        for url in urls {
            let clean = url.standardizedFileURL.resolvingSymlinksInPath()
            if jobs.contains(where: { $0.url == clean && ($0.state == "Na fila" || $0.state == "Convertendo") }) { continue }
            jobs.append(Job(url: clean))
        }
        startNext()
    }
    func startNext() {
        guard process == nil, !stopping, let index = jobs.firstIndex(where: { $0.state == "Na fila" }) else { return }
        running = true
        jobs[index].state = "Convertendo"
        let id = jobs[index].id
        activeID = id
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        task.arguments = [Bundle.main.resourceURL!.appendingPathComponent("worker.py").path, jobs[index].url.path]
        task.environment = ProcessInfo.processInfo.environment.merging(["PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"]) { _, new in new }
        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = pipe
        process = task
        do { try task.run() } catch {
            jobs[index].state = "Erro"
            jobs[index].error = error.localizedDescription
            process = nil; running = false; activeID = nil
            startNext(); return
        }
        DispatchQueue.global(qos: .userInitiated).async {
            var pending = Data()
            while true {
                let chunk = pipe.fileHandleForReading.availableData
                if chunk.isEmpty { break }
                pending.append(chunk)
                while let newline = pending.firstIndex(of: 10) {
                    let line = pending.subdata(in: 0..<newline)
                    pending.removeSubrange(0...newline)
                    if let event = try? JSONSerialization.jsonObject(with: line) as? [String: Any] {
                        DispatchQueue.main.async { self.receive(event, id: id) }
                    }
                }
            }
            task.waitUntilExit()
            let code = task.terminationStatus
            DispatchQueue.main.async { self.finish(id: id, code: code) }
        }
    }
    func receive(_ event: [String: Any], id: UUID) {
        guard let index = jobs.firstIndex(where: { $0.id == id }) else { return }
        if let progress = event["progress"] as? Double { jobs[index].progress = progress }
        if let output = event["output"] as? String { jobs[index].output = output }
        if let error = event["error"] as? String { jobs[index].error = error }
    }
    func finish(id: UUID, code: Int32) {
        if let index = jobs.firstIndex(where: { $0.id == id }) {
            jobs[index].state = code == 0 ? "Concluído" : (stopping || code == 130 ? "Cancelado" : "Erro")
            if code == 0 { jobs[index].progress = 1 }
            if code != 0 && jobs[index].error == nil && !stopping { jobs[index].error = "A conversão terminou com código \(code)." }
        }
        process = nil; activeID = nil; running = false; stopping = false
        startNext()
    }
    func cancel() {
        stopping = true
        for index in jobs.indices where jobs[index].state == "Na fila" { jobs[index].state = "Cancelado" }
        if let task = process, task.isRunning { task.terminate() }
        else { stopping = false; running = false }
    }
    func chooseFiles() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.allowedFileTypes = ["mov", "mp4", "m4v"]
        panel.directoryURL = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Movies/Vídeos/Source")
        if panel.runModal() == .OK { add(panel.urls) }
    }
}

struct ContentView: View {
    @ObservedObject var model: QueueModel
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Preview mínimo").font(.largeTitle).bold()
                    Text("Vídeo de 320 px · 8 fps · Áudio original").foregroundColor(.secondary)
                }
                Spacer()
                Button("Adicionar vídeos…") { model.chooseFiles() }
            }
            HStack {
                Text(model.stopping ? "Cancelando…" : model.running ? "Convertendo vídeos" : model.jobs.isEmpty ? "Selecione vídeos pelo Finder ou adicione aqui" : "Fila finalizada")
                Spacer()
                Text("\(model.completed) de \(model.jobs.count) concluídos").foregroundColor(.secondary)
            }
            ProgressView(value: model.totalProgress)
            List(model.jobs) { job in
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(job.url.lastPathComponent).fontWeight(.medium)
                        Spacer()
                        Text(job.state == "Convertendo" ? "\(Int(job.progress * 100))%" : job.state)
                            .foregroundColor(job.state == "Erro" ? .red : .secondary)
                    }
                    Text(job.url.deletingLastPathComponent().lastPathComponent).font(.caption).foregroundColor(.secondary)
                    if job.state == "Convertendo" { ProgressView(value: job.progress) }
                    if let error = job.error { Text(error).font(.caption).foregroundColor(.red).textSelection(.enabled) }
                    if job.state == "Concluído", let path = job.output {
                        Button("Mostrar no Finder") { NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: path)]) }.buttonStyle(.link)
                    }
                }.padding(.vertical, 6)
            }.listStyle(.inset)
            HStack {
                Text("Salvos em Preview, mantendo as subpastas de Source.").font(.caption).foregroundColor(.secondary)
                Spacer()
                Button("Cancelar fila") { model.cancel() }.disabled(!model.running || model.stopping)
            }
        }.padding(24).frame(minWidth: 700, minHeight: 430)
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    let model = QueueModel()
    var window: NSWindow?
    func showWindow() {
        if window == nil {
            let win = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 800, height: 540), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
            win.title = "Preview mínimo"
            win.contentView = NSHostingView(rootView: ContentView(model: model))
            win.isReleasedWhenClosed = false
            win.delegate = self
            win.center()
            window = win
        }
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    func applicationDidFinishLaunching(_ notification: Notification) { showWindow() }
    func application(_ sender: NSApplication, openFiles filenames: [String]) {
        showWindow()
        model.add(filenames.map { URL(fileURLWithPath: $0) })
        sender.reply(toOpenOrPrint: .success)
    }
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool { showWindow(); return true }
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        if model.running { sender.miniaturize(nil); return false }
        return true
    }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if model.running {
            model.cancel()
            Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { timer in
                if !self.model.running { timer.invalidate(); sender.reply(toApplicationShouldTerminate: true) }
            }
            return .terminateLater
        }
        return .terminateNow
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
let menu = NSMenu()
let appMenu = NSMenu()
appMenu.addItem(withTitle: "Sair do Preview mínimo", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
let item = NSMenuItem()
item.submenu = appMenu
menu.addItem(item)
app.mainMenu = menu
app.run()

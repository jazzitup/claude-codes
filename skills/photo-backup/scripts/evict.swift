import Foundation
import FileProvider

// Evict a File-Provider-backed item (Dropbox, Google Drive, iCloud, ...) back
// to "online only" — removes the local cached copy without touching the
// cloud copy. This is the same public API Finder's "Remove Download" uses.
//
// Usage: swift evict.swift <path> [<path> ...]

let args = Array(CommandLine.arguments.dropFirst())
guard !args.isEmpty else {
    FileHandle.standardError.write("usage: evict.swift <path> [<path> ...]\n".data(using: .utf8)!)
    exit(1)
}

func evict(_ path: String, completion: @escaping (Bool, String) -> Void) {
    let url = URL(fileURLWithPath: path)
    NSFileProviderManager.getIdentifierForUserVisibleFile(at: url) { identifier, domainIdentifier, error in
        if let error = error {
            completion(false, "resolve error: \(error.localizedDescription)")
            return
        }
        guard let identifier = identifier, let domainIdentifier = domainIdentifier else {
            completion(false, "could not resolve file provider identifier (not a File Provider item?)")
            return
        }
        let domain = NSFileProviderDomain(identifier: domainIdentifier, displayName: "")
        guard let manager = NSFileProviderManager(for: domain) else {
            completion(false, "no NSFileProviderManager for domain \(domainIdentifier.rawValue)")
            return
        }
        manager.evictItem(identifier: identifier) { error in
            if let error = error {
                completion(false, "evict error: \(error.localizedDescription)")
            } else {
                completion(true, "evicted")
            }
        }
    }
}

var remaining = args.count
let sem = DispatchSemaphore(value: 0)

for path in args {
    evict(path) { ok, msg in
        print("\(ok ? "OK" : "FAIL")\t\(path)\t\(msg)")
        remaining -= 1
        if remaining == 0 { sem.signal() }
    }
}

sem.wait()

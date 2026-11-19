// Reads text from an image with macOS Vision and prints JSON lines:
// {"t": text, "x": left, "y": top, "w": width, "h": height} in image pixels.
// Tall images are read in overlapping tiles so small logo text is not lost.
// Build: swiftc -O scripts/ocr.swift -o scripts/bin/ocr
import Foundation
import Vision
import ImageIO

let args = CommandLine.arguments
guard args.count > 1,
      let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: args[1]) as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
    FileHandle.standardError.write("usage: ocr <image>\n".data(using: .utf8)!)
    exit(1)
}

let width = image.width, height = image.height
let tile = 1200, overlap = 150
var top = 0
while top < height {
    let h = min(tile, height - top)
    if let crop = image.cropping(to: CGRect(x: 0, y: top, width: width, height: h)) {
        let req = VNRecognizeTextRequest()
        req.recognitionLevel = .accurate
        req.usesLanguageCorrection = false
        try? VNImageRequestHandler(cgImage: crop, options: [:]).perform([req])
        for obs in req.results ?? [] {
            guard let cand = obs.topCandidates(1).first else { continue }
            let b = obs.boundingBox
            let row: [String: Any] = [
                "t": cand.string,
                "x": Int(b.minX * CGFloat(width)),
                "y": top + Int((1 - b.maxY) * CGFloat(h)),
                "w": Int(b.width * CGFloat(width)),
                "h": Int(b.height * CGFloat(h)),
            ]
            if let d = try? JSONSerialization.data(withJSONObject: row), let s = String(data: d, encoding: .utf8) {
                print(s)
            }
        }
    }
    if top + h >= height { break }
    top += tile - overlap
}

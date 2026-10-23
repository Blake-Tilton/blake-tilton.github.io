// usage: poster <in> <out.png> <seconds>
import AVFoundation; import ImageIO; import UniformTypeIdentifiers
let a = CommandLine.arguments
let g = AVAssetImageGenerator(asset: AVURLAsset(url: URL(fileURLWithPath: a[1])))
g.appliesPreferredTrackTransform = true; g.requestedTimeToleranceBefore = .zero; g.requestedTimeToleranceAfter = .zero
let img = try! g.copyCGImage(at: CMTime(seconds: Double(a[3])!, preferredTimescale: 600), actualTime: nil)
let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[2]) as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(d, img, nil); CGImageDestinationFinalize(d)

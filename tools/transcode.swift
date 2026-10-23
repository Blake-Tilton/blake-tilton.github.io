// usage: transcode <in> <out.mp4> <maxWidth> <videoKbps> <audio:0|1>
import AVFoundation
let a = CommandLine.arguments
let src = AVURLAsset(url: URL(fileURLWithPath: a[1])), out = URL(fileURLWithPath: a[2])
let maxW = Double(a[3])!, kbps = Int(a[4])!, wantAudio = a[5] == "1"
try? FileManager.default.removeItem(at: out)
let sem = DispatchSemaphore(value: 0)
nonisolated(unsafe) var keep: [AnyObject] = []
Task {
  let vt = try await src.loadTracks(withMediaType: .video).first!
  let size = try await vt.load(.naturalSize).applying(try await vt.load(.preferredTransform))
  let w0 = abs(size.width), h0 = abs(size.height), sc = min(1, maxW / w0)
  let w = Int((w0 * sc / 2).rounded()) * 2, h = Int((h0 * sc / 2).rounded()) * 2
  let reader = try AVAssetReader(asset: src), writer = try AVAssetWriter(outputURL: out, fileType: .mp4)
  writer.shouldOptimizeForNetworkUse = true; keep += [reader, writer]
  let vout = AVAssetReaderTrackOutput(track: vt, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange])
  reader.add(vout)
  let vin = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h, AVVideoScalingModeKey: AVVideoScalingModeResizeAspect,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: kbps * 1000, AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel, AVVideoMaxKeyFrameIntervalDurationKey: 2]])
  vin.expectsMediaDataInRealTime = false; writer.add(vin)
  var aout: AVAssetReaderTrackOutput?, ain: AVAssetWriterInput?
  if wantAudio, let at = try await src.loadTracks(withMediaType: .audio).first {
    aout = AVAssetReaderTrackOutput(track: at, outputSettings: [AVFormatIDKey: kAudioFormatLinearPCM, AVLinearPCMBitDepthKey: 16, AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false, AVLinearPCMIsNonInterleaved: false, AVSampleRateKey: 48000, AVNumberOfChannelsKey: 2]); reader.add(aout!)
    ain = AVAssetWriterInput(mediaType: .audio, outputSettings: [AVFormatIDKey: kAudioFormatMPEG4AAC, AVNumberOfChannelsKey: 2, AVSampleRateKey: 48000, AVEncoderBitRateKey: 128000]); writer.add(ain!)
  }
  guard reader.startReading() else { print("reader fail", reader.error!); exit(1) }; writer.startWriting(); writer.startSession(atSourceTime: .zero)
  let g = DispatchGroup()
  func pump(_ i: AVAssetWriterInput, _ o: AVAssetReaderOutput, _ q: String) {
    g.enter(); i.requestMediaDataWhenReady(on: DispatchQueue(label: q)) {
      while i.isReadyForMoreMediaData { if let b = o.copyNextSampleBuffer() { i.append(b) } else { i.markAsFinished(); g.leave(); return } } } }
  pump(vin, vout, "v"); if let ai = ain, let ao = aout { pump(ai, ao, "a") }
  g.notify(queue: .main) { writer.finishWriting { print(writer.status == .completed ? "ok \(w)x\(h)" : "fail \(String(describing: writer.error))"); sem.signal() } }
}
DispatchQueue.global().async { sem.wait(); exit(0) }
dispatchMain()

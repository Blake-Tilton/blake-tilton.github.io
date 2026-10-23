import Foundation; import CoreGraphics; import ImageIO; import UniformTypeIdentifiers
let doc = CGPDFDocument(URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL)!
for i in 1...doc.numberOfPages { let p = doc.page(at: i)!; let r = p.getBoxRect(.mediaBox); let s: CGFloat = 1600/r.width
 let ctx = CGContext(data: nil, width: Int(r.width*s), height: Int(r.height*s), bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
 ctx.setFillColor(CGColor(red:1,green:1,blue:1,alpha:1)); ctx.fill(CGRect(x:0,y:0,width:r.width*s,height:r.height*s)); ctx.scaleBy(x: s, y: s); ctx.drawPDFPage(p)
 let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: CommandLine.arguments[2]+"/p\(i).png") as CFURL, UTType.png.identifier as CFString, 1, nil)!; CGImageDestinationAddImage(d, ctx.makeImage()!, nil); CGImageDestinationFinalize(d) }

import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'api_service.dart';
import 'camera_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load server IP from assets/config.json before anything else
  await ApiService.init();

  final cameras = await availableCameras();

  runApp(VisionAidApp(cameras: cameras));
}

class VisionAidApp extends StatelessWidget {
  final List<CameraDescription> cameras;

  const VisionAidApp({Key? key, required this.cameras}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VisionAid',
      theme: ThemeData.dark(),
      home: cameras.isEmpty
          ? const Scaffold(body: Center(child: Text("No camera found")))
          : CameraScreen(cameras: cameras),
    );
  }
}

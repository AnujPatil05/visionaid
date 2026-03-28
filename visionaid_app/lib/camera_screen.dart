import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:flutter/services.dart';
import 'api_service.dart';

class CameraScreen extends StatefulWidget {
  final List<CameraDescription> cameras;

  const CameraScreen({Key? key, required this.cameras}) : super(key: key);

  @override
  _CameraScreenState createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  late CameraController _ctrl;
  final FlutterTts _tts = FlutterTts();
  String _status = 'Hold steady to scan';
  String _lastSpeech = '';
  bool _isDanger = false;
  bool _isScanning = false;
  Timer? _scanTimer;

  @override
  void initState() {
    super.initState();
    _setupTts();
    _initCamera();
  }

  Future<void> _setupTts() async {
    await _tts.setLanguage("en-US");
    await _tts.setSpeechRate(0.45);
    await _tts.setVolume(1.0);
  }

  Future<void> _initCamera() async {
    _ctrl = CameraController(widget.cameras[0], ResolutionPreset.medium);
    await _ctrl.initialize();
    if (!mounted) return;
    setState(() {});

    Future.delayed(const Duration(milliseconds: 500), () {
      _tts.speak("VisionAid is ready. Point your camera at a sign and hold steady.");
      _scheduleScan();
    });
  }

  void _scheduleScan() {
    _scanTimer?.cancel();
    _scanTimer = Timer(const Duration(milliseconds: 1500), () {
      if (!_isScanning && mounted) {
        _runScan();
      }
    });
  }

  Future<void> _runScan() async {
    if (!_ctrl.value.isInitialized || _isScanning) return;

    _scanTimer?.cancel();

    setState(() {
      _isScanning = true;
      _status = 'Scanning…';
    });

    try {
      final img = await _ctrl.takePicture();
      final response = await ApiService.processFrame(File(img.path));

      final action = response['action'];
      if (action == 'spoken') {
        final bool danger = response['is_danger'] ?? false;
        final String speech = response['speech'] ?? '';
        final String lang = response['lang'] ?? 'en';

        if (danger) {
          HapticFeedback.heavyImpact();
          await Future.delayed(const Duration(milliseconds: 300));
          HapticFeedback.heavyImpact();
        }

        await _tts.setLanguage(lang == 'hi' ? 'hi-IN' : 'en-IN');
        await _tts.setSpeechRate(danger ? 0.38 : 0.45);
        await _tts.speak(speech);

        setState(() {
          _lastSpeech = speech;
          _isDanger = danger;
          _status = 'Scan complete';
        });
      } else if (action == 'none' || action == 'low_confidence') {
        final msg = "No sign found. Try again.";
        await _tts.setLanguage("en-US");
        await _tts.setSpeechRate(0.45);
        await _tts.speak(msg);
        
        setState(() {
          _status = 'No signs detected';
          _lastSpeech = '';
          _isDanger = false;
        });
      } else if (action == 'error') {
        await _tts.setLanguage("en-US");
        await _tts.setSpeechRate(0.45);
        await _tts.speak("Server disconnected. Check WiFi.");
        setState(() {
          _status = 'Server Connection Error';
        });
      }
    } catch (e) {
      await _tts.setLanguage("en-US");
      await _tts.speak("Network failure. Trying to reconnect.");
      setState(() {
        _status = 'Error during scan';
      });
    } finally {
      setState(() {
        _isScanning = false;
      });
      Future.delayed(const Duration(seconds: 4), () {
        if (mounted) _scheduleScan();
      });
    }
  }

  @override
  void dispose() {
    _scanTimer?.cancel();
    _ctrl.dispose();
    _tts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_ctrl.value.isInitialized) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: Colors.white)),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // 1. Camera preview
          SizedBox.expand(
            // ADA Fix: TalkBack labels the raw camera feed canvas.
            child: Semantics(
              label: 'Camera viewfinder',
              child: CameraPreview(_ctrl),
            ),
          ),
          
          // 2. CircularProgressIndicator if scanning
          if (_isScanning)
            Center(
              // ADA Fix: Labels visually abstract loading circles with explicit TTS context.
              child: Semantics(
                label: 'Scanning in progress',
                child: const CircularProgressIndicator(color: Colors.white),
              ),
            ),
            
          // 3. Bottom overlay
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              color: _isDanger 
                  ? Colors.red.withOpacity(0.88) 
                  : Colors.black.withOpacity(0.72),
              padding: const EdgeInsets.symmetric(vertical: 24.0, horizontal: 16.0),
              // ADA Fix: liveRegion forces immediate TalkBack announcements when inner text resets.
              child: Semantics(
                liveRegion: true,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _status,
                      // ADA Fix: Status increased to >= 18sp minimum bounds for low-vision reading.
                      style: const TextStyle(fontSize: 18, color: Colors.white70),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _lastSpeech.isNotEmpty ? _lastSpeech : 'Point camera at a sign',
                      // Defaults to 20sp, comfortably passes the 18sp minimum scale check.
                      style: const TextStyle(
                        fontSize: 20, 
                        fontWeight: FontWeight.bold, 
                        color: Colors.white
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ),
          
          // 4. Top-right scan button
          Positioned(
            top: 48,
            right: 16,
            // ADA Fix: Allows focus-stepping, marks trait as a button, removes reliance on visual center_focus_strong icon.
            child: Semantics(
              label: 'Scan now',
              button: true,
              child: GestureDetector(
                onTap: _runScan,
                child: Container(
                  width: 64,
                  height: 64,
                  decoration: const BoxDecoration(
                    color: Colors.black54,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.center_focus_strong,
                    color: Colors.white,
                    size: 32,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

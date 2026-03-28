import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:flutter/services.dart';
import 'package:sensors_plus/sensors_plus.dart';
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
  bool _isDescribingScene = false;

  Timer? _scanTimer;

  // Shake-to-replay state
  bool _canShake = true;
  StreamSubscription? _accelSub;

  @override
  void initState() {
    super.initState();
    _setupTts();
    _initCamera();
    _setupShakeDetector();
  }

  Future<void> _setupTts() async {
    await _tts.setLanguage("en-US");
    await _tts.setSpeechRate(0.45);
    await _tts.setVolume(1.0);
  }

  void _setupShakeDetector() {
    _accelSub = accelerometerEventStream(
      samplingPeriod: SensorInterval.normalInterval,
    ).listen((AccelerometerEvent event) {
      final double force =
          event.x.abs() + event.y.abs() + event.z.abs();

      // Gravity is ~9.8 m/s²; a good shake pushes well above 25 total
      if (force > 25 && _canShake && !_isScanning && !_isDescribingScene) {
        _canShake = false;
        HapticFeedback.mediumImpact();
        _tts.speak(
          _lastSpeech.isEmpty ? "Nothing detected yet." : _lastSpeech,
        );
        // 2-second cooldown prevents repeated triggers while shaking
        Future.delayed(
          const Duration(seconds: 2),
          () {
            if (mounted) setState(() => _canShake = true);
          },
        );
      }
    });
  }

  Future<void> _initCamera() async {
    _ctrl = CameraController(widget.cameras[0], ResolutionPreset.medium);
    await _ctrl.initialize();
    if (!mounted) return;
    setState(() {});

    Future.delayed(const Duration(milliseconds: 500), () {
      _tts.speak(
        "VisionAid is ready. "
        "Point your camera at a sign and hold steady. "
        "Double tap anywhere to describe your surroundings. "
        "Shake the phone to repeat the last announcement.",
      );
      _scheduleScan();
    });
  }

  void _scheduleScan() {
    _scanTimer?.cancel();
    _scanTimer = Timer(const Duration(milliseconds: 1500), () {
      if (!_isScanning && !_isDescribingScene && mounted) {
        _runScan();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Sign scan (existing pipeline)
  // ---------------------------------------------------------------------------
  Future<void> _runScan() async {
    if (!_ctrl.value.isInitialized || _isScanning || _isDescribingScene) return;

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
        setState(() {
          _status = 'No signs detected';
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
      // 'buffering' and 'dedup' — no feedback, just continue
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

  // ---------------------------------------------------------------------------
  // Scene summary (double-tap — "What's around me?")
  // ---------------------------------------------------------------------------
  Future<void> _runSceneSummary() async {
    if (!_ctrl.value.isInitialized || _isScanning || _isDescribingScene) return;

    _scanTimer?.cancel();

    setState(() {
      _isDescribingScene = true;
      _status = 'Describing scene…';
    });

    HapticFeedback.lightImpact();

    try {
      final img = await _ctrl.takePicture();
      final summary = await ApiService.sceneDescribe(File(img.path));

      await _tts.setLanguage("en-IN");
      await _tts.setSpeechRate(0.45);
      await _tts.speak(summary);

      setState(() {
        _lastSpeech = summary;
        _isDanger = false;
        _status = 'Scene scanned';
      });
    } catch (e) {
      await _tts.speak("Could not describe the scene. Check your connection.");
      setState(() {
        _status = 'Scene scan failed';
      });
    } finally {
      setState(() {
        _isDescribingScene = false;
      });
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) _scheduleScan();
      });
    }
  }

  @override
  void dispose() {
    _scanTimer?.cancel();
    _accelSub?.cancel();
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

    final bool busy = _isScanning || _isDescribingScene;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Semantics(
        label: 'Double tap to describe surroundings',
        child: GestureDetector(
          onDoubleTap: _runSceneSummary,
          child: Stack(
            children: [
              // 1. Camera preview
              SizedBox.expand(
                child: Semantics(
                  label: 'Camera viewfinder',
                  child: CameraPreview(_ctrl),
                ),
              ),

              // 2. Spinner while scanning or describing
              if (busy)
                Center(
                  child: Semantics(
                    label: _isDescribingScene
                        ? 'Describing scene in progress'
                        : 'Scanning in progress',
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
                      : _isDescribingScene
                          ? Colors.indigo.withOpacity(0.88)
                          : Colors.black.withOpacity(0.72),
                  padding: const EdgeInsets.symmetric(
                      vertical: 24.0, horizontal: 16.0),
                  child: Semantics(
                    liveRegion: true,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          _status,
                          style: const TextStyle(
                              fontSize: 18, color: Colors.white70),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _lastSpeech.isNotEmpty
                              ? _lastSpeech
                              : 'Point camera at a sign',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              // 4. Top-right manual scan button
              Positioned(
                top: 48,
                right: 16,
                child: Semantics(
                  label: 'Scan now. Long press to replay last announcement.',
                  button: true,
                  child: GestureDetector(
                    onTap: _runScan,
                    onLongPress: () {
                      HapticFeedback.mediumImpact();
                      _tts.speak(
                        _lastSpeech.isEmpty
                            ? "Nothing yet."
                            : _lastSpeech,
                      );
                    },
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

              // 5. Top-left scene describe button (visual affordance)
              Positioned(
                top: 48,
                left: 16,
                child: Semantics(
                  label: 'Describe surroundings',
                  button: true,
                  child: GestureDetector(
                    onTap: _runSceneSummary,
                    child: Container(
                      width: 64,
                      height: 64,
                      decoration: const BoxDecoration(
                        color: Colors.indigo,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.travel_explore,
                        color: Colors.white,
                        size: 30,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

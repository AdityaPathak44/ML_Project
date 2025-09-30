import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  Alert,
  PermissionsAndroid,
  Platform,
} from 'react-native';
import { RNCamera } from 'react-native-camera';
import Svg, { Line, Circle } from 'react-native-svg';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Push-up angle thresholds
const PUSHUP_THRESHOLDS = {
  Elbow: { Min: 62.2, Max: 161.5 },
  Shoulder: { Min: 4.6, Max: 65.2 },
  Back: { Min: 172.5, Max: 179.7 }
};

// MediaPipe Pose landmark indices
const POSE_LANDMARKS = {
  LEFT_SHOULDER: 11,
  RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13,
  RIGHT_ELBOW: 14,
  LEFT_WRIST: 15,
  RIGHT_WRIST: 16,
  LEFT_HIP: 23,
  RIGHT_HIP: 24,
  LEFT_KNEE: 25,
  RIGHT_KNEE: 26,
  LEFT_ANKLE: 27,
  RIGHT_ANKLE: 28
};

// Pose connections for stick figure visualization
const POSE_CONNECTIONS = [
  // Torso
  [POSE_LANDMARKS.LEFT_SHOULDER, POSE_LANDMARKS.RIGHT_SHOULDER],
  [POSE_LANDMARKS.LEFT_SHOULDER, POSE_LANDMARKS.LEFT_HIP],
  [POSE_LANDMARKS.RIGHT_SHOULDER, POSE_LANDMARKS.RIGHT_HIP],
  [POSE_LANDMARKS.LEFT_HIP, POSE_LANDMARKS.RIGHT_HIP],
  
  // Left arm
  [POSE_LANDMARKS.LEFT_SHOULDER, POSE_LANDMARKS.LEFT_ELBOW],
  [POSE_LANDMARKS.LEFT_ELBOW, POSE_LANDMARKS.LEFT_WRIST],
  
  // Right arm
  [POSE_LANDMARKS.RIGHT_SHOULDER, POSE_LANDMARKS.RIGHT_ELBOW],
  [POSE_LANDMARKS.RIGHT_ELBOW, POSE_LANDMARKS.RIGHT_WRIST],
  
  // Left leg
  [POSE_LANDMARKS.LEFT_HIP, POSE_LANDMARKS.LEFT_KNEE],
  [POSE_LANDMARKS.LEFT_KNEE, POSE_LANDMARKS.LEFT_ANKLE],
  
  // Right leg
  [POSE_LANDMARKS.RIGHT_HIP, POSE_LANDMARKS.RIGHT_KNEE],
  [POSE_LANDMARKS.RIGHT_KNEE, POSE_LANDMARKS.RIGHT_ANKLE],
];

/**
 * TensorFlow Lite Manager Class
 * Simulates low-level TFLite model loading and inference
 */
class TFLiteManager {
  constructor() {
    this.modelLoaded = false;
    this.modelPath = null;
  }

  async loadModel(modelPath) {
    try {
      // Simulate model loading process
      console.log(`Loading TFLite model from: ${modelPath}`);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate loading time
      this.modelPath = modelPath;
      this.modelLoaded = true;
      console.log('TFLite Pose model loaded successfully');
      return true;
    } catch (error) {
      console.error('Failed to load TFLite model:', error);
      return false;
    }
  }

  async runInference(frameData) {
    if (!this.modelLoaded) {
      throw new Error('Model not loaded');
    }

    // Simulate TFLite inference process
    // In real implementation, this would:
    // 1. Preprocess frame data (resize, normalize)
    // 2. Run inference on TFLite interpreter
    // 3. Post-process output to get landmarks
    
    return this.generateSimulatedPoseData();
  }

  generateSimulatedPoseData() {
    // Generate realistic pose landmarks for push-up position
    // Simulating a person in various push-up stages
    const baseTime = Date.now() / 1000;
    const cycleTime = (baseTime % 4); // 4-second cycle
    
    // Simulate push-up motion with elbow angle changing
    const pushupProgress = (Math.sin(cycleTime * Math.PI / 2) + 1) / 2;
    const elbowAngle = 62.2 + (161.5 - 62.2) * pushupProgress;
    
    // Generate normalized landmarks (0-1 coordinates)
    const landmarks = new Array(33).fill(null).map((_, index) => {
      let x = 0.5, y = 0.5, confidence = 0.8;
      
      switch (index) {
        case POSE_LANDMARKS.LEFT_SHOULDER:
          x = 0.35; y = 0.3; break;
        case POSE_LANDMARKS.RIGHT_SHOULDER:
          x = 0.65; y = 0.3; break;
        case POSE_LANDMARKS.LEFT_ELBOW:
          x = 0.25; y = 0.4 + (pushupProgress * 0.1); break;
        case POSE_LANDMARKS.RIGHT_ELBOW:
          x = 0.75; y = 0.4 + (pushupProgress * 0.1); break;
        case POSE_LANDMARKS.LEFT_WRIST:
          x = 0.15; y = 0.55 + (pushupProgress * 0.15); break;
        case POSE_LANDMARKS.RIGHT_WRIST:
          x = 0.85; y = 0.55 + (pushupProgress * 0.15); break;
        case POSE_LANDMARKS.LEFT_HIP:
          x = 0.4; y = 0.6; break;
        case POSE_LANDMARKS.RIGHT_HIP:
          x = 0.6; y = 0.6; break;
        case POSE_LANDMARKS.LEFT_KNEE:
          x = 0.38; y = 0.8; break;
        case POSE_LANDMARKS.RIGHT_KNEE:
          x = 0.62; y = 0.8; break;
        case POSE_LANDMARKS.LEFT_ANKLE:
          x = 0.36; y = 0.95; break;
        case POSE_LANDMARKS.RIGHT_ANKLE:
          x = 0.64; y = 0.95; break;
        default:
          confidence = 0.5; // Lower confidence for other landmarks
      }
      
      return { x, y, confidence };
    });
    
    return { landmarks, elbowAngle };
  }
}

/**
 * Calculate angle between three points using vector mathematics
 * @param {Object} A - First point {x, y}
 * @param {Object} B - Middle point (vertex) {x, y}
 * @param {Object} C - Third point {x, y}
 * @returns {number} - Angle in degrees
 */
const calculateAngle = (A, B, C) => {
  // Vector from B to A
  const BA = { x: A.x - B.x, y: A.y - B.y };
  // Vector from B to C
  const BC = { x: C.x - B.x, y: C.y - B.y };
  
  // Calculate dot product
  const dotProduct = BA.x * BC.x + BA.y * BC.y;
  
  // Calculate magnitudes
  const magnitudeBA = Math.sqrt(BA.x * BA.x + BA.y * BA.y);
  const magnitudeBC = Math.sqrt(BC.x * BC.x + BC.y * BC.y);
  
  // Calculate angle in radians
  const angleRad = Math.acos(dotProduct / (magnitudeBA * magnitudeBC));
  
  // Convert to degrees
  const angleDeg = (angleRad * 180) / Math.PI;
  
  return isNaN(angleDeg) ? 0 : angleDeg;
};

/**
 * Custom hook for TensorFlow Lite pose detection
 */
const useTFLitePoseDetection = () => {
  const [tfliteManager] = useState(() => new TFLiteManager());
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initializeTFLite = async () => {
      const success = await tfliteManager.loadModel('assets/pose_detection.tflite');
      setIsInitialized(success);
    };
    
    initializeTFLite();
  }, [tfliteManager]);

  const detectPose = useCallback(async (frameData) => {
    if (!isInitialized) {
      return null;
    }
    
    try {
      return await tfliteManager.runInference(frameData);
    } catch (error) {
      console.error('Pose detection error:', error);
      return null;
    }
  }, [isInitialized, tfliteManager]);

  return { detectPose, isInitialized };
};

/**
 * Stick Figure Component for pose visualization
 */
const StickFigure = ({ landmarks, screenWidth, screenHeight }) => {
  if (!landmarks || landmarks.length === 0) {
    return null;
  }

  const scaleX = (x) => x * screenWidth;
  const scaleY = (y) => y * screenHeight;

  return (
    <Svg 
      height={screenHeight} 
      width={screenWidth} 
      style={StyleSheet.absoluteFillObject}
      pointerEvents="none"
    >
      {/* Draw connections */}
      {POSE_CONNECTIONS.map(([startIdx, endIdx], index) => {
        const start = landmarks[startIdx];
        const end = landmarks[endIdx];
        
        if (!start || !end || start.confidence < 0.5 || end.confidence < 0.5) {
          return null;
        }
        
        return (
          <Line
            key={`connection-${index}`}
            x1={scaleX(start.x)}
            y1={scaleY(start.y)}
            x2={scaleX(end.x)}
            y2={scaleY(end.y)}
            stroke="#00ff00"
            strokeWidth="3"
            strokeOpacity="0.8"
          />
        );
      })}
      
      {/* Draw landmarks */}
      {landmarks.map((landmark, index) => {
        if (!landmark || landmark.confidence < 0.5) {
          return null;
        }
        
        return (
          <Circle
            key={`landmark-${index}`}
            cx={scaleX(landmark.x)}
            cy={scaleY(landmark.y)}
            r="6"
            fill="#ff0000"
            fillOpacity="0.8"
            stroke="#ffffff"
            strokeWidth="2"
          />
        );
      })}
    </Svg>
  );
};

/**
 * Main App Component
 */
const App = () => {
  const [repCounter, setRepCounter] = useState(0);
  const [stage, setStage] = useState('');
  const [elbowAngle, setElbowAngle] = useState(0);
  const [backAngle, setBackAngle] = useState(0);
  const [landmarks, setLandmarks] = useState([]);
  const [cameraPermission, setCameraPermission] = useState(false);
  
  const cameraRef = useRef(null);
  const { detectPose, isInitialized } = useTFLitePoseDetection();
  const stageRef = useRef('');
  const repCountRef = useRef(0);

  // Request camera permissions
  useEffect(() => {
    const requestCameraPermission = async () => {
      if (Platform.OS === 'android') {
        try {
          const granted = await PermissionsAndroid.request(
            PermissionsAndroid.PERMISSIONS.CAMERA,
            {
              title: 'Camera Permission',
              message: 'This app needs access to your camera to track push-ups',
              buttonNeutral: 'Ask Me Later',
              buttonNegative: 'Cancel',
              buttonPositive: 'OK',
            },
          );
          setCameraPermission(granted === PermissionsAndroid.RESULTS.GRANTED);
        } catch (err) {
          console.warn(err);
          setCameraPermission(false);
        }
      } else {
        setCameraPermission(true);
      }
    };

    requestCameraPermission();
  }, []);

  // Process camera frames for pose detection
  const processCameraFrame = useCallback(async ({ uri }) => {
    if (!isInitialized) {
      return;
    }

    try {
      // In real implementation, convert camera frame to tensor format
      const poseData = await detectPose(uri);
      
      if (poseData && poseData.landmarks) {
        const { landmarks: detectedLandmarks } = poseData;
        setLandmarks(detectedLandmarks);
        
        // Calculate angles
        const leftShoulder = detectedLandmarks[POSE_LANDMARKS.LEFT_SHOULDER];
        const leftElbow = detectedLandmarks[POSE_LANDMARKS.LEFT_ELBOW];
        const leftWrist = detectedLandmarks[POSE_LANDMARKS.LEFT_WRIST];
        const leftHip = detectedLandmarks[POSE_LANDMARKS.LEFT_HIP];
        const leftKnee = detectedLandmarks[POSE_LANDMARKS.LEFT_KNEE];
        
        if (leftShoulder && leftElbow && leftWrist && 
            leftShoulder.confidence > 0.5 && leftElbow.confidence > 0.5 && leftWrist.confidence > 0.5) {
          
          const currentElbowAngle = calculateAngle(leftShoulder, leftElbow, leftWrist);
          setElbowAngle(currentElbowAngle);
          
          // Rep counting logic
          if (currentElbowAngle > PUSHUP_THRESHOLDS.Elbow.Max) {
            stageRef.current = 'UP';
            setStage('UP');
          }
          
          if (currentElbowAngle < PUSHUP_THRESHOLDS.Elbow.Min && stageRef.current === 'UP') {
            stageRef.current = 'DOWN';
            setStage('DOWN');
            repCountRef.current += 1;
            setRepCounter(repCountRef.current);
          }
        }
        
        // Calculate back angle for form feedback
        if (leftShoulder && leftHip && leftKnee && 
            leftShoulder.confidence > 0.5 && leftHip.confidence > 0.5 && leftKnee.confidence > 0.5) {
          
          const currentBackAngle = calculateAngle(leftShoulder, leftHip, leftKnee);
          setBackAngle(currentBackAngle);
        }
      }
    } catch (error) {
      console.error('Frame processing error:', error);
    }
  }, [detectPose, isInitialized]);

  // Simulate continuous frame processing
  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    const interval = setInterval(() => {
      processCameraFrame({ uri: 'simulated_frame' });
    }, 100); // Process at ~10 FPS

    return () => clearInterval(interval);
  }, [isInitialized, processCameraFrame]);

  if (!cameraPermission) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>
          Camera permission required for push-up tracking
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Camera View */}
      <RNCamera
        ref={cameraRef}
        style={styles.camera}
        type={RNCamera.Constants.Type.front}
        flashMode={RNCamera.Constants.FlashMode.off}
        androidCameraPermissionOptions={{
          title: 'Permission to use camera',
          message: 'We need your permission to use your camera',
          buttonPositive: 'Ok',
          buttonNegative: 'Cancel',
        }}
      />
      
      {/* Stick Figure Overlay */}
      <StickFigure 
        landmarks={landmarks} 
        screenWidth={screenWidth} 
        screenHeight={screenHeight} 
      />
      
      {/* Stats Overlay */}
      <View style={styles.statsContainer}>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>REPS</Text>
          <Text style={styles.statValue}>{repCounter}</Text>
        </View>
        
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>STAGE</Text>
          <Text style={[styles.statValue, { color: stage === 'UP' ? '#4CAF50' : '#FF9800' }]}>
            {stage || 'READY'}
          </Text>
        </View>
      </View>
      
      <View style={styles.angleContainer}>
        <View style={styles.angleBox}>
          <Text style={styles.angleLabel}>ELBOW ANGLE</Text>
          <Text style={styles.angleValue}>{elbowAngle.toFixed(1)}°</Text>
        </View>
        
        <View style={styles.angleBox}>
          <Text style={styles.angleLabel}>BACK ANGLE</Text>
          <Text style={styles.angleValue}>{backAngle.toFixed(1)}°</Text>
        </View>
      </View>
      
      {/* Initialization Status */}
      {!isInitialized && (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading TensorFlow Lite Model...</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  permissionText: {
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
    margin: 20,
  },
  statsContainer: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statBox: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    minWidth: 120,
  },
  statLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  statValue: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
  },
  angleContainer: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  angleBox: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    minWidth: 100,
  },
  angleLabel: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 3,
  },
  angleValue: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loadingContainer: {
    position: 'absolute',
    bottom: 30,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    fontSize: 14,
  },
});

export default App;

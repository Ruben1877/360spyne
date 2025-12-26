/**
 * Capture Screen - Clone Spyne Mobile
 * ====================================
 * Guided camera capture with overlay silhouettes.
 * Replicates Spyne's capture experience exactly.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Camera, CameraType, FlashMode } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type RootStackParamList = {
  Capture: { vehicleId?: string; vehicleType?: string };
  Preview: { photos: string[]; vehicleId?: string };
};

type Props = NativeStackScreenProps<RootStackParamList, 'Capture'>;

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Capture angle configuration (like Spyne's 8-point system)
const ANGLES = [
  { id: 0, name: 'Front', angle: 0, instruction: 'Position yourself directly in front of the vehicle' },
  { id: 1, name: 'Front Right', angle: 45, instruction: 'Move 45° to the right of the front' },
  { id: 2, name: 'Right Side', angle: 90, instruction: 'Position yourself at the right side' },
  { id: 3, name: 'Rear Right', angle: 135, instruction: 'Move 45° towards the rear right' },
  { id: 4, name: 'Rear', angle: 180, instruction: 'Position yourself directly behind the vehicle' },
  { id: 5, name: 'Rear Left', angle: 225, instruction: 'Move 45° towards the rear left' },
  { id: 6, name: 'Left Side', angle: 270, instruction: 'Position yourself at the left side' },
  { id: 7, name: 'Front Left', angle: 315, instruction: 'Move 45° to the left of the front' },
];

// Silhouette overlays from Spyne's S3 (remote URLs)
const SILHOUETTES: Record<string, string[]> = {
  sedan: [
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/1.png',  // Front
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/5.png',  // Front Right
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/10.png', // Right
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/14.png', // Rear Right
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/19.png', // Rear
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/23.png', // Rear Left
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/28.png', // Left
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/32.png', // Front Left
  ],
  suv: [
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/1.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/5.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/10.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/14.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/19.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/23.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/28.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/suv/32.png',
  ],
  hatchback: [
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/1.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/5.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/10.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/14.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/19.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/23.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/28.png',
    'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/32.png',
  ],
};

export default function CaptureScreen({ navigation, route }: Props) {
  const vehicleId = route.params?.vehicleId;
  const vehicleType = route.params?.vehicleType || 'sedan';
  const cameraRef = useRef<Camera>(null);
  
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [currentAngleIndex, setCurrentAngleIndex] = useState(0);
  const [photos, setPhotos] = useState<string[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [flashMode, setFlashMode] = useState<FlashMode>(FlashMode.off);
  const [showOverlay, setShowOverlay] = useState(true);

  const currentAngle = ANGLES[currentAngleIndex];
  const progress = ((currentAngleIndex) / ANGLES.length) * 100;

  // Request camera permission
  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  // Take photo
  const takePhoto = async () => {
    if (!cameraRef.current || isCapturing) return;

    setIsCapturing(true);

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.9,
        base64: false,
        exif: true,
      });

      const newPhotos = [...photos, photo.uri];
      setPhotos(newPhotos);

      // Vibrate for feedback
      // Vibration.vibrate(50);

      // Move to next angle or complete
      if (currentAngleIndex < ANGLES.length - 1) {
        setCurrentAngleIndex(currentAngleIndex + 1);
      } else {
        // All photos captured - navigate to preview
        navigation.navigate('Preview', { 
          photos: newPhotos, 
          vehicleId 
        });
      }
    } catch (error) {
      console.error('Failed to take photo:', error);
      Alert.alert('Error', 'Failed to capture photo. Please try again.');
    } finally {
      setIsCapturing(false);
    }
  };

  // Toggle flash
  const toggleFlash = () => {
    setFlashMode(current => 
      current === FlashMode.off ? FlashMode.on : FlashMode.off
    );
  };

  // Skip current angle
  const skipAngle = () => {
    if (currentAngleIndex < ANGLES.length - 1) {
      setCurrentAngleIndex(currentAngleIndex + 1);
    }
  };

  // Go back to previous angle
  const previousAngle = () => {
    if (currentAngleIndex > 0) {
      setCurrentAngleIndex(currentAngleIndex - 1);
      // Remove the last photo
      setPhotos(photos.slice(0, -1));
    }
  };

  // Cancel capture
  const handleCancel = () => {
    Alert.alert(
      'Cancel Capture?',
      'Your progress will be lost.',
      [
        { text: 'Continue', style: 'cancel' },
        { text: 'Cancel', style: 'destructive', onPress: () => navigation.goBack() },
      ]
    );
  };

  // Permission denied
  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <View style={styles.permissionDenied}>
          <Ionicons name="camera-off" size={64} color="#6b7280" />
          <Text style={styles.permissionText}>Camera permission denied</Text>
          <Text style={styles.permissionSubtext}>
            Please enable camera access in your device settings.
          </Text>
        </View>
      </View>
    );
  }

  // Loading
  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#0ea5e9" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Camera */}
      <Camera
        ref={cameraRef}
        style={styles.camera}
        type={CameraType.back}
        flashMode={flashMode}
      >
        {/* Overlay silhouette */}
        {showOverlay && SILHOUETTES[vehicleType]?.[currentAngleIndex] && (
          <View style={styles.overlayContainer}>
            <Image
              source={{ uri: SILHOUETTES[vehicleType][currentAngleIndex] }}
              style={styles.overlayImage}
              resizeMode="contain"
            />
          </View>
        )}

        {/* Top bar */}
        <View style={styles.topBar}>
          <TouchableOpacity onPress={handleCancel} style={styles.topButton}>
            <Ionicons name="close" size={28} color="white" />
          </TouchableOpacity>

          <View style={styles.angleIndicator}>
            <Text style={styles.angleNumber}>
              {currentAngleIndex + 1} / {ANGLES.length}
            </Text>
            <Text style={styles.angleName}>{currentAngle.name}</Text>
          </View>

          <TouchableOpacity onPress={toggleFlash} style={styles.topButton}>
            <Ionicons
              name={flashMode === FlashMode.on ? 'flash' : 'flash-off'}
              size={24}
              color="white"
            />
          </TouchableOpacity>
        </View>

        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress}%` }]} />
          </View>
        </View>

        {/* Instruction */}
        <View style={styles.instructionContainer}>
          <Text style={styles.instructionText}>{currentAngle.instruction}</Text>
        </View>

        {/* Bottom controls */}
        <View style={styles.bottomControls}>
          {/* Previous button */}
          <TouchableOpacity
            onPress={previousAngle}
            disabled={currentAngleIndex === 0}
            style={[styles.sideButton, currentAngleIndex === 0 && styles.disabledButton]}
          >
            <Ionicons name="arrow-back" size={24} color="white" />
          </TouchableOpacity>

          {/* Capture button */}
          <TouchableOpacity
            onPress={takePhoto}
            disabled={isCapturing}
            style={styles.captureButton}
          >
            <View style={styles.captureButtonInner}>
              {isCapturing ? (
                <ActivityIndicator color="#0a0f1a" />
              ) : (
                <View style={styles.captureButtonCenter} />
              )}
            </View>
          </TouchableOpacity>

          {/* Skip button */}
          <TouchableOpacity
            onPress={skipAngle}
            disabled={currentAngleIndex === ANGLES.length - 1}
            style={[
              styles.sideButton,
              currentAngleIndex === ANGLES.length - 1 && styles.disabledButton,
            ]}
          >
            <Ionicons name="arrow-forward" size={24} color="white" />
          </TouchableOpacity>
        </View>

        {/* Toggle overlay button */}
        <TouchableOpacity
          onPress={() => setShowOverlay(!showOverlay)}
          style={styles.toggleOverlay}
        >
          <Ionicons
            name={showOverlay ? 'eye' : 'eye-off'}
            size={20}
            color="white"
          />
          <Text style={styles.toggleOverlayText}>
            {showOverlay ? 'Hide Guide' : 'Show Guide'}
          </Text>
        </TouchableOpacity>

        {/* Captured photos preview */}
        <View style={styles.photosPreview}>
          {photos.slice(-3).map((uri, index) => (
            <View key={index} style={styles.photoThumb}>
              <Image source={{ uri }} style={styles.photoThumbImage} />
            </View>
          ))}
        </View>
      </Camera>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0f1a',
  },
  camera: {
    flex: 1,
  },
  overlayContainer: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  overlayImage: {
    width: SCREEN_WIDTH * 0.9,
    height: SCREEN_HEIGHT * 0.5,
    opacity: 0.5,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 50,
    paddingHorizontal: 20,
  },
  topButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  angleIndicator: {
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  angleNumber: {
    color: '#0ea5e9',
    fontSize: 18,
    fontWeight: 'bold',
  },
  angleName: {
    color: 'white',
    fontSize: 14,
  },
  progressContainer: {
    paddingHorizontal: 20,
    marginTop: 20,
  },
  progressBar: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#0ea5e9',
    borderRadius: 2,
  },
  instructionContainer: {
    position: 'absolute',
    bottom: 180,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  instructionText: {
    color: 'white',
    fontSize: 14,
    textAlign: 'center',
  },
  bottomControls: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  sideButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  disabledButton: {
    opacity: 0.3,
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'white',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#0ea5e9',
  },
  captureButtonInner: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: 'white',
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureButtonCenter: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#0ea5e9',
  },
  toggleOverlay: {
    position: 'absolute',
    top: 120,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  toggleOverlayText: {
    color: 'white',
    fontSize: 12,
    marginLeft: 6,
  },
  photosPreview: {
    position: 'absolute',
    bottom: 130,
    left: 20,
    flexDirection: 'row',
  },
  photoThumb: {
    width: 40,
    height: 40,
    borderRadius: 8,
    overflow: 'hidden',
    marginRight: 8,
    borderWidth: 2,
    borderColor: 'white',
  },
  photoThumbImage: {
    width: '100%',
    height: '100%',
  },
  permissionDenied: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  permissionText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 20,
  },
  permissionSubtext: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 10,
  },
});


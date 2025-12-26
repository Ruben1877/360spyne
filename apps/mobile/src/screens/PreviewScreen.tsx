/**
 * Preview Screen - Clone Spyne Mobile
 * ====================================
 * Review captured photos before uploading.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  Image,
  Dimensions,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const THUMB_SIZE = (SCREEN_WIDTH - 60) / 4;

type RootStackParamList = {
  Capture: { vehicleId?: string; vehicleType?: string };
  Preview: { photos: string[]; vehicleId?: string };
};

type Props = NativeStackScreenProps<RootStackParamList, 'Preview'>;

export default function PreviewScreen({ navigation, route }: Props) {
  const { photos, vehicleId } = route.params;
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const ANGLES = [
    'Front', 'Front Right', 'Right Side', 'Rear Right',
    'Rear', 'Rear Left', 'Left Side', 'Front Left'
  ];

  const handleUpload = async () => {
    Alert.alert(
      'Upload Photos',
      `Upload ${photos.length} photos for processing?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Upload',
          onPress: async () => {
            setIsUploading(true);
            try {
              // Simulate upload progress
              for (let i = 0; i <= photos.length; i++) {
                setUploadProgress((i / photos.length) * 100);
                await new Promise(resolve => setTimeout(resolve, 500));
              }
              
              // TODO: Implement actual upload to API
              Alert.alert(
                '✅ Upload Complete!', 
                'Your photos are being processed. You will receive a notification when ready.',
                [{ text: 'OK', onPress: () => navigation.navigate('Capture', {}) }]
              );
            } catch (error) {
              Alert.alert('Upload Failed', 'Please check your connection and try again.');
            } finally {
              setIsUploading(false);
              setUploadProgress(0);
            }
          },
        },
      ]
    );
  };

  const handleRetake = () => {
    Alert.alert(
      'Retake Photo',
      `Retake the ${ANGLES[selectedIndex]} photo?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Retake', 
          onPress: () => navigation.goBack()
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerButton}>
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Review Photos</Text>
        <View style={styles.headerButton} />
      </View>

      {/* Main preview */}
      <View style={styles.mainPreview}>
        <Image
          source={{ uri: photos[selectedIndex] }}
          style={styles.mainImage}
          resizeMode="contain"
        />
        <View style={styles.angleLabel}>
          <Text style={styles.angleLabelText}>
            {selectedIndex + 1}. {ANGLES[selectedIndex]}
          </Text>
        </View>
      </View>

      {/* Thumbnail grid */}
      <View style={styles.thumbnailContainer}>
        <FlatList
          data={photos}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.thumbnailList}
          keyExtractor={(_, index) => index.toString()}
          renderItem={({ item, index }) => (
            <TouchableOpacity
              onPress={() => setSelectedIndex(index)}
              style={[
                styles.thumbnailWrapper,
                selectedIndex === index && styles.thumbnailSelected,
              ]}
            >
              <Image source={{ uri: item }} style={styles.thumbnail} />
              <View style={styles.thumbnailNumber}>
                <Text style={styles.thumbnailNumberText}>{index + 1}</Text>
              </View>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity onPress={handleRetake} style={styles.retakeButton}>
          <Ionicons name="camera-reverse" size={20} color="#0ea5e9" />
          <Text style={styles.retakeButtonText}>Retake</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={handleUpload}
          disabled={isUploading}
          style={styles.uploadButton}
        >
          {isUploading ? (
            <View style={styles.uploadingContainer}>
              <ActivityIndicator color="white" size="small" />
              <Text style={styles.uploadButtonText}>
                {Math.round(uploadProgress)}%
              </Text>
            </View>
          ) : (
            <>
              <Ionicons name="cloud-upload" size={20} color="white" />
              <Text style={styles.uploadButtonText}>
                Upload All ({photos.length})
              </Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Upload progress overlay */}
      {isUploading && (
        <View style={styles.uploadOverlay}>
          <View style={styles.uploadCard}>
            <ActivityIndicator size="large" color="#0ea5e9" />
            <Text style={styles.uploadTitle}>Uploading Photos</Text>
            <View style={styles.uploadProgressBar}>
              <View
                style={[
                  styles.uploadProgressFill,
                  { width: `${uploadProgress}%` },
                ]}
              />
            </View>
            <Text style={styles.uploadProgressText}>
              {Math.round(uploadProgress)}% complete
            </Text>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0f1a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 50,
    paddingHorizontal: 20,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  headerButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  mainPreview: {
    flex: 1,
    margin: 20,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#111827',
  },
  mainImage: {
    flex: 1,
  },
  angleLabel: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  angleLabelText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  thumbnailContainer: {
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  thumbnailList: {
    paddingHorizontal: 20,
  },
  thumbnailWrapper: {
    width: THUMB_SIZE,
    height: THUMB_SIZE,
    marginRight: 10,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  thumbnailSelected: {
    borderColor: '#0ea5e9',
  },
  thumbnail: {
    width: '100%',
    height: '100%',
  },
  thumbnailNumber: {
    position: 'absolute',
    top: 4,
    left: 4,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  thumbnailNumberText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  actions: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 20,
    paddingBottom: 40,
    gap: 12,
  },
  retakeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#0ea5e9',
    gap: 8,
  },
  retakeButtonText: {
    color: '#0ea5e9',
    fontSize: 16,
    fontWeight: '600',
  },
  uploadButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#0ea5e9',
    gap: 8,
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  uploadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  uploadOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  uploadCard: {
    backgroundColor: '#1f2937',
    padding: 40,
    borderRadius: 20,
    alignItems: 'center',
    width: SCREEN_WIDTH - 80,
  },
  uploadTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 20,
    marginBottom: 20,
  },
  uploadProgressBar: {
    width: '100%',
    height: 8,
    backgroundColor: '#374151',
    borderRadius: 4,
    overflow: 'hidden',
  },
  uploadProgressFill: {
    height: '100%',
    backgroundColor: '#0ea5e9',
    borderRadius: 4,
  },
  uploadProgressText: {
    color: '#9ca3af',
    fontSize: 14,
    marginTop: 12,
  },
});

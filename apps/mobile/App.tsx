/**
 * Clone Spyne Mobile App
 * ======================
 * Entry point for the mobile application
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import CaptureScreen from './src/screens/CaptureScreen';
import PreviewScreen from './src/screens/PreviewScreen';

export type RootStackParamList = {
  Capture: { vehicleId?: string; vehicleType?: string };
  Preview: { photos: string[]; vehicleId?: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <StatusBar style="light" />
        <Stack.Navigator
          initialRouteName="Capture"
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: '#0a0f1a' },
            animation: 'slide_from_right',
          }}
        >
          <Stack.Screen
            name="Capture"
            component={CaptureScreen}
            initialParams={{ vehicleType: 'sedan' }}
          />
          <Stack.Screen
            name="Preview"
            component={PreviewScreen}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}


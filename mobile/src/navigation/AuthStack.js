import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoginScreen from '../screens/LoginScreen';
import SignupScreen from '../screens/SignupScreen';
import OtpScreen from '../screens/OtpScreen';
import { ROUTES } from '../constants/routes';
const Stack = createNativeStackNavigator();
export default function AuthStack() {
  return <Stack.Navigator screenOptions={{ headerBackTitle: 'Back' }}>
    <Stack.Screen name={ROUTES.LOGIN} component={LoginScreen} options={{ title: 'Sign in' }} />
    <Stack.Screen name={ROUTES.SIGNUP} component={SignupScreen} options={{ title: 'Create account' }} />
    <Stack.Screen name={ROUTES.OTP} component={OtpScreen} options={{ title: 'Verify mobile' }} />
  </Stack.Navigator>;
}

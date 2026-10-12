import React,{useState} from 'react';
import {Alert,ScrollView,Text} from 'react-native';
import {authApi} from '../services/authApi';
import {useAuth} from '../store/auth';
import FormField from '../components/FormField';
import ActionButton from '../components/ActionButton';
import {errorText} from '../utils/ui';
import {styles} from '../styles/screens/OtpScreen.styles';
export default function OtpScreen({route,navigation}) {
 const mobile=route.params?.mobile;const [otp,setOtp]=useState(''),[busy,setBusy]=useState(false);const {signIn}=useAuth();
 async function submit(){if(!/^\d{6}$/.test(otp)){Alert.alert('Invalid OTP','Enter the 6-digit code.');return;}
 setBusy(true);try{await signIn(mobile,otp);navigation.getParent()?.goBack();}catch(e){Alert.alert('Verification failed',errorText(e));}finally{setBusy(false);}}
 async function resend(){try{await authApi.sendOtp(mobile);Alert.alert('OTP sent','Check your phone.');}catch(e){Alert.alert('Please wait',errorText(e));}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Verify mobile</Text><Text style={styles.subtitle}>Enter the OTP sent to {mobile}</Text><FormField label="6-digit OTP" value={otp} onChangeText={setOtp} keyboardType="number-pad" maxLength={6}/><ActionButton title="Verify & sign in" onPress={submit} loading={busy}/><ActionButton title="Resend OTP" onPress={resend} secondary/></ScrollView>;
}

import React,{useState} from 'react';
import {Alert,ScrollView,Text} from 'react-native';
import {authApi} from '../services/authApi';
import FormField from '../components/FormField';
import ActionButton from '../components/ActionButton';
import {errorText} from '../utils/ui';
import {styles} from '../styles/screens/LoginScreen.styles';
export default function LoginScreen({navigation}) {
 const [mobile,setMobile]=useState('');const [busy,setBusy]=useState(false);
 async function submit(){if(!/^[6-9]\d{9}$/.test(mobile)){Alert.alert('Invalid mobile','Enter a valid 10-digit Indian mobile number.');return;}
 setBusy(true);try{await authApi.sendOtp(mobile);navigation.navigate('Otp',{mobile});}catch(e){Alert.alert('Unable to send OTP',errorText(e));}finally{setBusy(false);}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Welcome back</Text><Text style={styles.subtitle}>Sign in with a mobile OTP. No password needed.</Text><FormField label="Mobile number" keyboardType="phone-pad" maxLength={10} value={mobile} onChangeText={setMobile}/><ActionButton title="Send OTP" onPress={submit} loading={busy}/><ActionButton title="New here? Create account" secondary onPress={()=>navigation.navigate('Signup')}/></ScrollView>;
}

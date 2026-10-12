import React,{useState} from 'react';
import {Alert,ScrollView,Text} from 'react-native';
import {authApi} from '../services/authApi';
import FormField from '../components/FormField';
import ActionButton from '../components/ActionButton';
import {errorText} from '../utils/ui';
import {styles} from '../styles/screens/SignupScreen.styles';
export default function SignupScreen({navigation}) {
 const [name,setName]=useState(''),[mobile,setMobile]=useState(''),[email,setEmail]=useState(''),[busy,setBusy]=useState(false);
 async function submit(){if(!name.trim()||!/^[6-9]\d{9}$/.test(mobile)||!/^\S+@\S+\.\S+$/.test(email)){Alert.alert('Check details','Enter your name, valid mobile and email.');return;}
 setBusy(true);try{await authApi.signup(name.trim(),mobile,email.trim());navigation.navigate('Otp',{mobile});}catch(e){Alert.alert('Signup failed',errorText(e));}finally{setBusy(false);}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Create account</Text><Text style={styles.subtitle}>Only your name, mobile and email are required.</Text><FormField label="Name" value={name} onChangeText={setName}/><FormField label="Mobile" value={mobile} onChangeText={setMobile} keyboardType="phone-pad" maxLength={10}/><FormField label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none"/><ActionButton title="Create account" onPress={submit} loading={busy}/></ScrollView>;
}

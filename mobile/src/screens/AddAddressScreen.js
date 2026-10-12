import React,{useState} from 'react';
import {Alert,ScrollView,Text} from 'react-native';
import {addressApi} from '../services/addressApi';
import FormField from '../components/FormField';
import ActionButton from '../components/ActionButton';
import {errorText} from '../utils/ui';
import {styles} from '../styles/screens/AddAddressScreen.styles';
const fields=[['recipient_name','Recipient name'],['phone','Mobile number'],['line1','Address line 1'],['line2','Address line 2'],['landmark','Landmark'],['city','City'],['state','State'],['postal_code','PIN code']];
export default function AddAddressScreen({navigation,route}) {
 const existing=route.params?.address;const [form,setForm]=useState(Object.fromEntries(fields.map(([key])=>[key,existing?.[key]||'']))),[isDefault,setIsDefault]=useState(existing?.is_default||false),[busy,setBusy]=useState(false);
 async function save(){if(!form.recipient_name||!form.line1||!form.city||!form.state||!/^[6-9]\d{9}$/.test(form.phone)||!/^[1-9]\d{5}$/.test(form.postal_code)){Alert.alert('Check address','Complete all required fields with valid mobile and PIN.');return;}
 setBusy(true);try{const payload={...form,is_default:isDefault};if(existing)await addressApi.update(existing.id,payload);else await addressApi.create(payload);navigation.goBack();}catch(e){Alert.alert('Could not save',errorText(e));}finally{setBusy(false);}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>{existing?'Edit':'Add'} address</Text>{fields.map(([key,label])=><FormField key={key} label={label} value={form[key]} onChangeText={v=>setForm(f=>({...f,[key]:v}))} keyboardType={key==='phone'||key==='postal_code'?'number-pad':'default'}/>)}<ActionButton title={isDefault?'✓ Default address':'Make default address'} secondary onPress={()=>setIsDefault(!isDefault)}/><ActionButton title="Save address" loading={busy} onPress={save}/></ScrollView>;
}

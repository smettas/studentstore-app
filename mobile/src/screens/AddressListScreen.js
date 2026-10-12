import React,{useCallback,useState} from 'react';
import {Alert,ScrollView,Text,View} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import {addressApi} from '../services/addressApi';
import ActionButton from '../components/ActionButton';
import ScreenState from '../components/ScreenState';
import {rows,errorText} from '../utils/ui';
import {styles} from '../styles/screens/AddressListScreen.styles';
export default function AddressListScreen({navigation,route}) {
 const [addresses,setAddresses]=useState([]),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const load=useCallback(async()=>{setLoading(true);try{setAddresses(rows(await addressApi.list()));setError('');}catch(e){setError(errorText(e));}finally{setLoading(false);}},[]);
 useFocusEffect(useCallback(()=>{load();},[load]));
 async function remove(id){try{await addressApi.remove(id);await load();}catch(e){Alert.alert('Error',errorText(e));}}
 async function setDefault(id){try{await addressApi.setDefault(id);await load();}catch(e){Alert.alert('Error',errorText(e));}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Delivery addresses</Text><ActionButton title="Add address" onPress={()=>navigation.navigate('AddAddress')}/><ScreenState loading={loading} error={error} empty={!loading&&!addresses.length?'No addresses yet.':''}/>{addresses.map(a=><View key={a.id} style={styles.card}><Text style={styles.section}>{a.recipient_name} {a.is_default?'(Default)':''}</Text><Text>{a.line1}, {a.line2}, {a.city}, {a.state} - {a.postal_code}</Text><Text>{a.phone}</Text>{route.params?.selectForCheckout?<ActionButton title="Deliver here" onPress={()=>navigation.navigate('Checkout',{addressId:a.id})}/>:null}<ActionButton title="Edit" secondary onPress={()=>navigation.navigate('AddAddress',{address:a})}/>{!a.is_default?<ActionButton title="Set default" secondary onPress={()=>setDefault(a.id)}/>:null}<ActionButton title="Delete" secondary onPress={()=>Alert.alert('Delete address?','This cannot be undone.',[{text:'Cancel'},{text:'Delete',style:'destructive',onPress:()=>remove(a.id)}])}/></View>)}</ScrollView>;
}

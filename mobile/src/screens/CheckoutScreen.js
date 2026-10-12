import React,{useCallback,useState} from 'react';
import {Alert,ScrollView,Text,View} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import {addressApi} from '../services/addressApi';
import {orderApi} from '../services/orderApi';
import {useCart} from '../store/cart';
import ActionButton from '../components/ActionButton';
import FormField from '../components/FormField';
import ScreenState from '../components/ScreenState';
import {rows,errorText,money} from '../utils/ui';
import {styles} from '../styles/screens/CheckoutScreen.styles';
export default function CheckoutScreen({navigation,route}) {
 const [addresses,setAddresses]=useState([]),[selected,setSelected]=useState(null),[coupon,setCoupon]=useState(''),[method,setMethod]=useState('cod'),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const {data,refresh}=useCart();
 useFocusEffect(useCallback(()=>{addressApi.list().then(v=>{const a=rows(v);setAddresses(a);setSelected(old=>route.params?.addressId||old||a.find(x=>x.is_default)?.id||a[0]?.id);}).catch(e=>setError(errorText(e)));refresh().catch(e=>setError(errorText(e)));},[route.params?.addressId,refresh]));
 async function submit(){if(!selected){Alert.alert('Address required','Add a delivery address first.');return;}if(!data?.items?.length){Alert.alert('Cart empty','Add products before checkout.');return;}
 setBusy(true);try{const order=await orderApi.create({address_id:selected,coupon_code:coupon.trim(),payment_method:method});navigation.replace('Payment',{order,method});}catch(e){Alert.alert('Checkout failed',errorText(e));}finally{setBusy(false);}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Checkout</Text><ScreenState error={error}/><Text style={styles.section}>Delivery address</Text>{addresses.map(a=><ActionButton key={a.id} secondary={selected!==a.id} title={`${selected===a.id?'✓ ':''}${a.recipient_name} — ${a.city}`} onPress={()=>setSelected(a.id)}/>)}<ActionButton title="Add new address" secondary onPress={()=>navigation.navigate('AddAddress')}/><Text style={styles.section}>Coupon</Text><FormField label="Coupon code (optional)" value={coupon} onChangeText={setCoupon} autoCapitalize="characters"/><Text style={styles.section}>Payment method</Text><ActionButton title={`${method==='cod'?'✓ ':''}Cash on Delivery`} secondary={method!=='cod'} onPress={()=>setMethod('cod')}/><ActionButton title={`${method==='razorpay'?'✓ ':''}Razorpay`} secondary={method!=='razorpay'} onPress={()=>setMethod('razorpay')}/><View style={styles.card}><Text>Cart subtotal: {money(data?.total)}</Text><Text style={styles.muted}>Final delivery fee and coupon discount are calculated by the server.</Text></View><ActionButton title="Place order" loading={busy} onPress={submit}/></ScrollView>;
}

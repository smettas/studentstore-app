import React,{useState} from 'react';
import {Alert,ScrollView,Text} from 'react-native';
import {paymentApi} from '../services/paymentApi';
import ActionButton from '../components/ActionButton';
import {money,errorText} from '../utils/ui';
import {styles} from '../styles/screens/PaymentScreen.styles';
export default function PaymentScreen({navigation,route}) {
 const {order,method}=route.params||{};const [busy,setBusy]=useState(false);
 async function confirmCOD(){setBusy(true);try{await paymentApi.confirmCod(order.id);Alert.alert('Order placed','Your Cash on Delivery order has been confirmed.');navigation.replace('OrderDetail',{id:order.id});}catch(e){Alert.alert('Could not confirm',errorText(e));}finally{setBusy(false);}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Payment</Text><Text style={styles.section}>Order #{order?.id}</Text><Text style={styles.subtitle}>Total: {money(order?.total)}</Text>{method==='cod'?<ActionButton title="Confirm Cash on Delivery" loading={busy} onPress={confirmCOD}/>:<><Text style={styles.card}>Online payment checkout is disabled until a compatible native Razorpay SDK is installed and verified. No payment has been collected.</Text><ActionButton title="View order status" secondary onPress={()=>navigation.replace('OrderDetail',{id:order.id})}/></>}</ScrollView>;
}

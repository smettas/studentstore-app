import React,{useCallback,useState} from 'react';
import {Alert,ScrollView,Text,View} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import {orderApi} from '../services/orderApi';
import ActionButton from '../components/ActionButton';
import ScreenState from '../components/ScreenState';
import {money,errorText} from '../utils/ui';
import {styles} from '../styles/screens/OrderDetailScreen.styles';
export default function OrderDetailScreen({route}) {
 const {id}=route.params||{};const [order,setOrder]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const load=useCallback(async()=>{setLoading(true);try{setOrder(await orderApi.detail(id));setError('');}catch(e){setError(errorText(e));}finally{setLoading(false);}},[id]);
 useFocusEffect(useCallback(()=>{load();},[load]));
 async function cancel(){try{await orderApi.cancel(id);await load();}catch(e){Alert.alert('Cancellation failed',errorText(e));}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><ScreenState loading={loading} error={error} onRetry={load}/>{order?<><Text style={styles.title}>Order #{order.id}</Text><Text style={styles.section}>Status: {order.status}</Text><Text>Payment: {order.payment_method||'Pending'}</Text><Text style={styles.section}>Items</Text>{order.items?.map(i=><View key={i.id} style={styles.card}><Text>{i.product_name} × {i.quantity}</Text><Text>{money(i.line_total)}</Text></View>)}<Text>Subtotal: {money(order.subtotal)}</Text><Text>Discount: {money(order.discount_total)}</Text><Text>Delivery: {money(order.shipping_fee)}</Text><Text style={styles.section}>Total: {money(order.total)}</Text><Text style={styles.section}>Delivery address</Text><Text>{order.shipping_address}</Text><Text style={styles.section}>Tracking history</Text>{order.status_history?.map((h,i)=><Text key={i} style={styles.card}>{h.status}: {h.note}</Text>)}{['pending','placed','confirmed'].includes(order.status)?<ActionButton title="Request cancellation" secondary onPress={()=>Alert.alert('Cancel order?','This cannot be undone.',[{text:'Keep order'},{text:'Cancel order',style:'destructive',onPress:cancel}])}/>:null}</>:null}</ScrollView>;
}

import React,{useCallback,useState} from 'react';
import {ScrollView,Text,View} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import {orderApi} from '../services/orderApi';
import ActionButton from '../components/ActionButton';
import ScreenState from '../components/ScreenState';
import {rows,money,errorText} from '../utils/ui';
import {styles} from '../styles/screens/OrderListScreen.styles';
export default function OrderListScreen({navigation}) {
 const [orders,setOrders]=useState([]),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const load=useCallback(async()=>{setLoading(true);try{setOrders(rows(await orderApi.list()));setError('');}catch(e){setError(errorText(e));}finally{setLoading(false);}},[]);
 useFocusEffect(useCallback(()=>{load();},[load]));
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>My orders</Text><ScreenState loading={loading} error={error} onRetry={load} empty={!loading&&!orders.length?'No orders yet.':''}/>{orders.map(o=><View key={o.id} style={styles.card}><Text style={styles.section}>Order #{o.id} · {o.status}</Text><Text>{money(o.total)}</Text><Text style={styles.muted}>{o.created_at?new Date(o.created_at).toLocaleDateString():''}</Text><ActionButton title="Track order" secondary onPress={()=>navigation.navigate('OrderDetail',{id:o.id})}/></View>)}</ScrollView>;
}

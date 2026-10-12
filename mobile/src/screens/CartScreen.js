import React,{useCallback,useState} from 'react';
import {Alert,ScrollView,Text,View} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import {cartApi} from '../services/cartApi';
import {useAuth} from '../store/auth';
import {useCart} from '../store/cart';
import ItemTile from '../components/ItemTile';
import ActionButton from '../components/ActionButton';
import ScreenState from '../components/ScreenState';
import {money,errorText} from '../utils/ui';
import {styles} from '../styles/screens/CartScreen.styles';
export default function CartScreen({navigation}) {
 const {isAuthenticated}=useAuth(),{data,refresh,loading}=useCart();const [error,setError]=useState('');
 useFocusEffect(useCallback(()=>{if(isAuthenticated)refresh().catch(e=>setError(errorText(e)));},[isAuthenticated,refresh]));
 async function change(item,quantity){try{if(quantity===0)await cartApi.remove(item.id);else await cartApi.update(item.id,quantity);await refresh();}catch(e){Alert.alert('Cart error',errorText(e));}}
 if(!isAuthenticated)return <View style={styles.content}><Text style={styles.title}>Your cart</Text><Text style={styles.subtitle}>Sign in when you're ready to add items.</Text><ActionButton title="Sign in" onPress={()=>navigation.navigate('Authentication')}/></View>;
 const items=data?.items||[];
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Your cart</Text><ScreenState loading={loading&&!data} error={error} empty={!loading&&!items.length?'Your cart is empty.':''}/>{items.map(item=><View key={item.id} style={styles.card}><ItemTile product={item.product} onPress={()=>navigation.navigate('ProductDetail',{slug:item.product.slug})}/><Text>Quantity: {item.quantity} · {money(item.line_total)}</Text><View style={styles.row}><ActionButton title="−" secondary onPress={()=>change(item,item.quantity-1)}/><ActionButton title="+" secondary onPress={()=>change(item,item.quantity+1)}/><ActionButton title="Remove" secondary onPress={()=>change(item,0)}/></View></View>)}{items.length?<><Text style={styles.section}>Subtotal: {money(data?.total)}</Text><ActionButton title="Proceed to checkout" onPress={()=>navigation.navigate('Checkout')}/></>:null}</ScrollView>;
}

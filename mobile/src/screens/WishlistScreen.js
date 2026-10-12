import React,{useCallback,useState} from 'react';
import {Alert,ScrollView,Text,View} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import {wishlistApi} from '../services/wishlistApi';
import {useWishlist} from '../store/wishlist';
import {useAuth} from '../store/auth';
import ItemTile from '../components/ItemTile';
import ActionButton from '../components/ActionButton';
import ScreenState from '../components/ScreenState';
import {errorText,rows} from '../utils/ui';
import {styles} from '../styles/screens/WishlistScreen.styles';
export default function WishlistScreen({navigation}) {
 const {isAuthenticated}=useAuth(),{data,refresh,loading}=useWishlist();const [error,setError]=useState('');
 useFocusEffect(useCallback(()=>{if(isAuthenticated)refresh().catch(e=>setError(errorText(e)));},[isAuthenticated,refresh]));
 async function remove(id){try{await wishlistApi.remove(id);await refresh();}catch(e){Alert.alert('Error',errorText(e));}}
 if(!isAuthenticated)return <View style={styles.content}><Text style={styles.title}>Wishlist</Text><ActionButton title="Sign in to save products" onPress={()=>navigation.navigate('Authentication')}/></View>;
 const items=rows(data);
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Wishlist</Text><ScreenState loading={loading&&!data} error={error} empty={!loading&&!items.length?'No saved products.':''}/>{items.map(item=><View key={item.id}><ItemTile product={item.product} onPress={()=>navigation.navigate('ProductDetail',{slug:item.product.slug})}/><ActionButton title="Remove" secondary onPress={()=>remove(item.id)}/></View>)}</ScrollView>;
}

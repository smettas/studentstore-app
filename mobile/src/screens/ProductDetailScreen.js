import React,{useEffect,useState} from 'react';
import {Alert,Image,ScrollView,Text,View} from 'react-native';
import {productApi} from '../services/productApi';
import {cartApi} from '../services/cartApi';
import {wishlistApi} from '../services/wishlistApi';
import {useAuth} from '../store/auth';
import {useCart} from '../store/cart';
import {useWishlist} from '../store/wishlist';
import ActionButton from '../components/ActionButton';
import ScreenState from '../components/ScreenState';
import {money,priceOf,errorText} from '../utils/ui';
import {styles} from '../styles/screens/ProductDetailScreen.styles';
export default function ProductDetailScreen({route,navigation}) {
 const {slug}=route.params||{};const [item,setItem]=useState(null),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const {isAuthenticated}=useAuth(),cart=useCart(),wishlist=useWishlist();
 useEffect(()=>{productApi.detail(slug).then(setItem).catch(e=>setError(errorText(e))).finally(()=>setLoading(false));},[slug]);
 async function action(type){if(!isAuthenticated){navigation.navigate('Authentication');return;}setBusy(true);try{if(type==='cart'){await cartApi.add(item.id);await cart.refresh();Alert.alert('Added to cart');}else{await wishlistApi.add(item.id);await wishlist.refresh();Alert.alert('Added to wishlist');}}catch(e){Alert.alert('Unable to add',errorText(e));}finally{setBusy(false);}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><ScreenState loading={loading} error={error}/>{item?<><Text style={styles.title}>{item.name}</Text>{item.images?.map(img=>img.image_url?<Image key={img.id} source={{uri:img.image_url}} style={{height:230,marginBottom:12,borderRadius:12}} resizeMode="contain"/>:null)}<Text style={styles.section}>{money(priceOf(item))}</Text><Text style={styles.subtitle}>{item.brand?.name||''} • {item.stock} in stock</Text><Text style={styles.card}>{item.description||'No description available.'}</Text><Text style={styles.subtitle}>Suitable for: {item.study_levels?.map(s=>s.name).join(', ')||'Everyone'}</Text><ActionButton title="Add to cart" disabled={!item.in_stock} loading={busy} onPress={()=>action('cart')}/><ActionButton title="Save to wishlist" secondary loading={busy} onPress={()=>action('wishlist')}/></>:null}</ScrollView>;
}

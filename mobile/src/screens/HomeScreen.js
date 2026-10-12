import React,{useCallback,useState} from 'react';
import {ScrollView,Text,Pressable,View} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import {productApi} from '../services/productApi';
import ItemTile from '../components/ItemTile';
import ScreenState from '../components/ScreenState';
import ActionButton from '../components/ActionButton';
import {rows,errorText} from '../utils/ui';
import {styles} from '../styles/screens/HomeScreen.styles';
export default function HomeScreen({navigation}) {
 const [products,setProducts]=useState([]),[categories,setCategories]=useState([]),[levels,setLevels]=useState([]),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const load=useCallback(async()=>{setLoading(true);setError('');try{const [p,c,l]=await Promise.all([productApi.list({}),productApi.categories(),productApi.studyLevels()]);setProducts(rows(p));setCategories(rows(c));setLevels(rows(l));}catch(e){setError(errorText(e));}finally{setLoading(false);}},[]);
 useFocusEffect(useCallback(()=>{load();},[load]));
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>StudentStore</Text><Text style={styles.subtitle}>Everything you need to learn. Shop any category.</Text><ActionButton title="Browse all products" onPress={()=>navigation.navigate('ProductList')}/><Text style={styles.section}>Categories</Text><View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{categories.map(c=><Pressable key={c.id} style={styles.card} onPress={()=>navigation.navigate('ProductList',{category:c.slug})}><Text>{c.name}</Text></Pressable>)}</View><Text style={styles.section}>Study levels</Text><View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{levels.map(l=><Pressable key={l.id} style={styles.card} onPress={()=>navigation.navigate('ProductList',{study_level:l.slug})}><Text>{l.name}</Text></Pressable>)}</View><Text style={styles.section}>Explore products</Text><ScreenState loading={loading} error={error} onRetry={load} empty={!products.length?'No products yet.':''}/>{products.slice(0,12).map(p=><ItemTile key={p.id} product={p} onPress={()=>navigation.navigate('ProductDetail',{slug:p.slug})}/>)}</ScrollView>;
}

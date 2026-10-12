import React,{useEffect,useState} from 'react';
import {ScrollView,Text} from 'react-native';
import {productApi} from '../services/productApi';
import ScreenState from '../components/ScreenState';
import ActionButton from '../components/ActionButton';
import {rows,errorText} from '../utils/ui';
import {styles} from '../styles/screens/CategoryScreen.styles';
export default function CategoryScreen({navigation}) {
 const [data,setData]=useState([]),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 useEffect(()=>{productApi.categories().then(v=>setData(rows(v))).catch(e=>setError(errorText(e))).finally(()=>setLoading(false));},[]);
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Categories</Text><ScreenState loading={loading} error={error} empty={!data.length?'No categories found.':''}/>{data.map(c=><ActionButton key={c.id} title={c.name} secondary onPress={()=>navigation.navigate('ProductList',{category:c.slug})}/>)}</ScrollView>;
}

import React,{useState} from 'react';
import {ScrollView,Text} from 'react-native';
import {productApi} from '../services/productApi';
import ItemTile from '../components/ItemTile';
import FormField from '../components/FormField';
import ActionButton from '../components/ActionButton';
import ScreenState from '../components/ScreenState';
import {rows,errorText} from '../utils/ui';
import {styles} from '../styles/screens/SearchScreen.styles';
export default function SearchScreen({navigation}) {
 const [q,setQ]=useState(''),[items,setItems]=useState([]),[searched,setSearched]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function search(){setBusy(true);setError('');setSearched(true);try{setItems(rows(await productApi.list({search:q.trim()})));}catch(e){setError(errorText(e));}finally{setBusy(false);}}
 return <ScrollView style={styles.container} contentContainerStyle={styles.content}><Text style={styles.title}>Search essentials</Text><FormField label="Search by name, brand or SKU" value={q} onChangeText={setQ} onSubmitEditing={search} returnKeyType="search"/><ActionButton title="Search" onPress={search} loading={busy}/><ScreenState error={error} empty={searched&&!busy&&!items.length?'No results found.':''}/>{items.map(p=><ItemTile key={p.id} product={p} onPress={()=>navigation.navigate('ProductDetail',{slug:p.slug})}/>)}</ScrollView>;
}

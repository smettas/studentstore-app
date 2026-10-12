import React from 'react';
import { Text, TextInput, View } from 'react-native';
import { colors } from '../constants/colors';
export default function FormField({label, value, onChangeText, ...props}) {
 return <View style={{marginBottom:12}}><Text style={{color:colors.text,fontWeight:'600',marginBottom:5}}>{label}</Text><TextInput value={value} onChangeText={onChangeText} placeholderTextColor={colors.muted} style={{backgroundColor:'#fff',borderWidth:1,borderColor:colors.border,borderRadius:10,padding:12,color:colors.text}} {...props}/></View>;
}

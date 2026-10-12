import React from 'react';
import { ActivityIndicator, Pressable, Text } from 'react-native';
import { colors } from '../constants/colors';
export default function ActionButton({title, onPress, disabled, loading, secondary = false}) {
 return <Pressable accessibilityRole="button" disabled={disabled || loading} onPress={onPress} style={{backgroundColor: secondary ? '#fff' : colors.primary, borderColor: colors.primary, borderWidth: 1, padding: 13, borderRadius: 12, marginVertical: 6, opacity: disabled ? .5 : 1}}>
 {loading ? <ActivityIndicator color={secondary ? colors.primary : '#fff'}/> : <Text style={{textAlign:'center', fontWeight:'700', color:secondary ? colors.primary : '#fff'}}>{title}</Text>}</Pressable>;
}

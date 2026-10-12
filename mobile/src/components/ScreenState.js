import React from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import ActionButton from './ActionButton';
export default function ScreenState({loading,error,empty,onRetry}) {
 if (!loading && !error && !empty) return null;
 return <View style={{padding:22,alignItems:'center'}}>{loading ? <ActivityIndicator size="large"/> : <Text style={{textAlign:'center',marginBottom:12}}>{error || empty}</Text>}{!loading && error && onRetry ? <ActionButton title="Try again" onPress={onRetry}/> : null}</View>;
}

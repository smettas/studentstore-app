import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';
export const styles = StyleSheet.create({
 container:{flex:1,backgroundColor:colors.background},
 content:{padding:16,paddingBottom:36},
 title:{fontSize:24,fontWeight:'800',color:colors.text,marginBottom:14},
 subtitle:{color:colors.muted,marginBottom:14},
 section:{fontSize:18,fontWeight:'700',color:colors.text,marginTop:14,marginBottom:10},
 card:{padding:14,backgroundColor:'#fff',borderRadius:12,marginBottom:12},
 row:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:10},
 muted:{color:colors.muted},
});

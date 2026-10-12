import { StyleSheet } from 'react-native';
import { colors } from '../constants/colors';

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: colors.background,
  },
  title: { fontSize: 30, fontWeight: '700', color: colors.primary },
  subtitle: { marginTop: 8, fontSize: 15, color: colors.muted },
});

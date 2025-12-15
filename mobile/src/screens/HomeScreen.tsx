import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, SafeAreaView } from 'react-native';
import { useNavigation } from '@react-navigation/native';

export default function HomeScreen() {
  const navigation = useNavigation<any>();

  const menuItems = [
    { title: '种羊档案', icon: '🐑', route: 'AnimalDetail', params: { id: 1 } },
    { title: '表型记录', icon: '📝', route: 'Phenotype' },
    { title: '育种评估', icon: '📊', route: 'Breeding' },
    { title: '扫码识别', icon: '📷', route: 'Scan' },
    { title: '系谱查询', icon: '🌳', route: 'Pedigree' },
    { title: '任务通知', icon: '🔔', route: 'Notification' }
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.welcomeText}>欢迎使用</Text>
          <Text style={styles.appName}>国际顶级肉羊育种系统</Text>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>1,248</Text>
            <Text style={styles.statLabel}>存栏总数</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>45</Text>
            <Text style={styles.statLabel}>今日新增</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>12</Text>
            <Text style={styles.statLabel}>待处理</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>常用功能</Text>
        <View style={styles.grid}>
          {menuItems.map((item, index) => (
            <TouchableOpacity 
              key={index} 
              style={styles.gridItem}
              onPress={() => item.route === 'AnimalDetail' ? 
                navigation.navigate(item.route, item.params) : 
                console.log('Navigating to', item.route)
              }
            >
              <Text style={styles.icon}>{item.icon}</Text>
              <Text style={styles.gridLabel}>{item.title}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    padding: 16,
  },
  header: {
    marginBottom: 24,
  },
  welcomeText: {
    fontSize: 16,
    color: '#666',
  },
  appName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1890ff',
  },
  statLabel: {
    fontSize: 12,
    color: '#888',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  gridItem: {
    width: '31%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 16,
    elevation: 1,
  },
  icon: {
    fontSize: 32,
    marginBottom: 8,
  },
  gridLabel: {
    fontSize: 14,
    color: '#333',
  },
});

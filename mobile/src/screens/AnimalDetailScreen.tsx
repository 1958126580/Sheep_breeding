import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, ActivityIndicator } from 'react-native';
import { useRoute } from '@react-navigation/native';
import client from '../api/client';

export default function AnimalDetailScreen() {
  const route = useRoute<any>();
  const { id } = route.params || { id: 1 };
  const [loading, setLoading] = useState(true);
  const [animal, setAnimal] = useState<any>(null);

  useEffect(() => {
    // 模拟数据加载
    setTimeout(() => {
      setAnimal({
        id: id,
        code: `SH2024${String(id).padStart(3, '0')}`,
        breed: '杜泊羊',
        gender: '公',
        birthDate: '2024-01-15',
        weight: '45.5 kg',
        breedingValue: '+2.5',
        healthStatus: '健康',
        blockchainHash: '0x7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069'
      });
      setLoading(false);
    }, 1000);

    // 实际API调用
    // client.get(`/animals/${id}`).then(...)
  }, [id]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1890ff" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <View style={styles.headerRow}>
          <Text style={styles.animalCode}>{animal.code}</Text>
          <View style={styles.tag}>
            <Text style={styles.tagText}>{animal.healthStatus}</Text>
          </View>
        </View>
        
        <View style={styles.infoRow}>
          <Text style={styles.label}>品种:</Text>
          <Text style={styles.value}>{animal.breed}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>性别:</Text>
          <Text style={styles.value}>{animal.gender}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>出生日期:</Text>
          <Text style={styles.value}>{animal.birthDate}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.label}>当前体重:</Text>
          <Text style={styles.value}>{animal.weight}</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>育种评估</Text>
        <View style={styles.ebvContainer}>
          <Text style={styles.ebvLabel}>综合育种值</Text>
          <Text style={styles.ebvValue}>{animal.breedingValue}</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>区块链溯源</Text>
        <Text style={styles.hashLabel}>交易哈希:</Text>
        <Text style={styles.hashValue}>{animal.blockchainHash}</Text>
        <View style={styles.verifiedBadge}>
          <Text style={styles.verifiedText}>✓ 已验证</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    paddingBottom: 12,
  },
  animalCode: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  tag: {
    backgroundColor: '#e6f7ff',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#91d5ff',
  },
  tagText: {
    color: '#1890ff',
    fontSize: 12,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  label: {
    width: 80,
    color: '#888',
    fontSize: 16,
  },
  value: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#333',
  },
  ebvContainer: {
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f6ffed',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#b7eb8f',
  },
  ebvLabel: {
    color: '#52c41a',
    marginBottom: 8,
  },
  ebvValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#52c41a',
  },
  hashLabel: {
    color: '#888',
    marginBottom: 4,
  },
  hashValue: {
    fontSize: 12,
    color: '#666',
    fontFamily: 'monospace',
    marginBottom: 12,
  },
  verifiedBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#f6ffed',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#b7eb8f',
  },
  verifiedText: {
    color: '#52c41a',
    fontSize: 12,
    fontWeight: 'bold',
  },
});

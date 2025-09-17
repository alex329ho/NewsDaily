import React, { useMemo, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  ActivityIndicator,
  Linking,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { fetchSummary } from './src/apiClient';

const DEFAULT_TOPICS = ['finance', 'economy', 'politics'];
const HOUR_OPTIONS = [4, 8, 12, 24];

function TopicChip({ label, selected, onPress }) {
  return (
    <Pressable
      style={[styles.chip, selected ? styles.chipSelected : null]}
      onPress={onPress}
    >
      <Text style={selected ? styles.chipLabelSelected : styles.chipLabel}>{label}</Text>
    </Pressable>
  );
}

function HeadlineItem({ headline }) {
  const handlePress = () => {
    if (headline.url) {
      Linking.openURL(headline.url).catch(() => {});
    }
  };

  return (
    <Pressable style={styles.headline} onPress={handlePress}>
      <Text style={styles.headlineTitle}>{headline.title || 'Untitled'}</Text>
      <Text style={styles.headlineMeta}>
        {headline.source_domain ? `${headline.source_domain} • ${headline.seendate}` : headline.seendate}
      </Text>
    </Pressable>
  );
}

export default function App() {
  const [selectedTopics, setSelectedTopics] = useState(new Set(DEFAULT_TOPICS));
  const [customTopic, setCustomTopic] = useState('');
  const [hours, setHours] = useState(8);
  const [region, setRegion] = useState('');
  const [language, setLanguage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const topicsArray = useMemo(() => Array.from(selectedTopics), [selectedTopics]);

  const toggleTopic = (topic) => {
    const next = new Set(selectedTopics);
    if (next.has(topic)) {
      next.delete(topic);
    } else {
      next.add(topic);
    }
    setSelectedTopics(next);
  };

  const addCustomTopic = () => {
    const trimmed = customTopic.trim();
    if (!trimmed) {
      return;
    }
    const next = new Set(selectedTopics);
    next.add(trimmed);
    setSelectedTopics(next);
    setCustomTopic('');
  };

  const fetchData = async () => {
    if (topicsArray.length === 0) {
      setError('Please select at least one topic.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const summary = await fetchSummary({
        topics: topicsArray,
        hours,
        region: region.trim() || undefined,
        language: language.trim() || undefined,
      });
      setResult(summary);
    } catch (err) {
      setResult(null);
      setError(err.message || 'Failed to fetch summary.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>DailyNews Mobile</Text>

        <Text style={styles.sectionTitle}>Topics</Text>
        <View style={styles.chipContainer}>
          {DEFAULT_TOPICS.map((topic) => (
            <TopicChip
              key={topic}
              label={topic}
              selected={selectedTopics.has(topic)}
              onPress={() => toggleTopic(topic)}
            />
          ))}
        </View>

        <View style={styles.row}>
          <TextInput
            style={[styles.input, styles.flex]}
            placeholder="Add custom topic"
            value={customTopic}
            onChangeText={setCustomTopic}
            onSubmitEditing={addCustomTopic}
          />
          <Pressable style={styles.addButton} onPress={addCustomTopic}>
            <Text style={styles.addButtonLabel}>Add</Text>
          </Pressable>
        </View>

        <Text style={styles.sectionTitle}>Hours</Text>
        <View style={styles.row}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.chipContainer}>
              {HOUR_OPTIONS.map((value) => (
                <TopicChip
                  key={value}
                  label={`${value}`}
                  selected={hours === value}
                  onPress={() => setHours(value)}
                />
              ))}
            </View>
          </ScrollView>
        </View>

        <Text style={styles.sectionTitle}>Region</Text>
        <TextInput
          style={styles.input}
          placeholder="Region code (optional)"
          value={region}
          onChangeText={setRegion}
        />

        <Text style={styles.sectionTitle}>Language</Text>
        <TextInput
          style={styles.input}
          placeholder="Language code (optional)"
          value={language}
          onChangeText={setLanguage}
        />

        <Pressable style={styles.fetchButton} onPress={fetchData} disabled={loading}>
          <Text style={styles.fetchButtonLabel}>{loading ? 'Loading…' : 'Fetch Summary'}</Text>
        </Pressable>

        {loading && <ActivityIndicator style={styles.loading} />}
        {error && <Text style={styles.error}>{error}</Text>}

        {result && !loading && (
          <View style={styles.summaryBlock}>
            <Text style={styles.summaryText}>{result.summary}</Text>
            <Text style={styles.sectionTitle}>Headlines</Text>
            {result.headlines.length === 0 ? (
              <Text style={styles.empty}>No headlines returned.</Text>
            ) : (
              result.headlines.map((headline, index) => (
                <HeadlineItem key={`${headline.url}-${index}`} headline={headline} />
              ))
            )}
          </View>
        )}

        {!result && !loading && !error && (
          <Text style={styles.empty}>Select topics and tap Fetch Summary to begin.</Text>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f7f8fb',
  },
  scrollContent: {
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 12,
  },
  sectionTitle: {
    marginTop: 16,
    marginBottom: 6,
    fontWeight: '600',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    margin: 4,
    backgroundColor: '#e0e0e0',
  },
  chipSelected: {
    backgroundColor: '#4c51bf',
  },
  chipLabel: {
    color: '#1a202c',
  },
  chipLabelSelected: {
    color: '#ffffff',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 8,
  },
  flex: {
    flex: 1,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    backgroundColor: '#ffffff',
  },
  addButton: {
    marginLeft: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#4c51bf',
  },
  addButtonLabel: {
    color: '#ffffff',
    fontWeight: '600',
  },
  fetchButton: {
    marginTop: 16,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    backgroundColor: '#2b6cb0',
  },
  fetchButtonLabel: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 16,
  },
  loading: {
    marginTop: 12,
  },
  error: {
    marginTop: 12,
    color: '#c53030',
  },
  summaryBlock: {
    marginTop: 24,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 2,
  },
  summaryText: {
    marginBottom: 16,
    fontSize: 16,
    lineHeight: 22,
  },
  headline: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headlineTitle: {
    fontWeight: '600',
    marginBottom: 4,
  },
  headlineMeta: {
    color: '#6b7280',
  },
  empty: {
    marginTop: 16,
    color: '#6b7280',
  },
});

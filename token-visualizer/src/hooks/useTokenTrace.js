
import { useState, useEffect } from 'react';
import { processTokenData } from '../utils/dataAdapter';

export const useTokenTrace = (url) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to load data: ${response.statusText}`);
        }
        const jsonData = await response.json();
        const processedData = processTokenData(jsonData);
        setData(processedData);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, loading, error };
};

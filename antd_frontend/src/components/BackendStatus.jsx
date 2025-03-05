import React, { useEffect, useState } from 'react';
import { Badge, Tooltip } from 'antd';

const BackendStatus = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/status')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch backend status');
        }
        return response.json();
      })
      .then(data => {
        setIsConnected(data.connected);
        setLoading(false);
      })
      .catch(() => {
        setIsConnected(false);
        setLoading(false);
      });
  }, []);

  return (
    <Tooltip title={loading ? "Checking backend status..." : (isConnected ? "Backend Connected" : "Backend Disconnected")}>
      <Badge status={isConnected ? "success" : "error"} />
    </Tooltip>
  );
};

export default BackendStatus;

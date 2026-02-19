import { Session, SessionsResponse } from '../../shared/models/sessions.model';

export const MOCK_SESSIONS: Session[] = [
  {
    session_id: 'c5df4999-b2b7-40ba-8e23-54f9d5baba9c',
    created_at: 1764156881,
    updated_at: 1764157279,
    summary: {
      title: 'Machine Learning Deep Dive'
    },
    metadata: null
  },
  {
    session_id: '83e95e65-45c3-4545-b2cf-815c435d69bd',
    created_at: 1764156324,
    updated_at: 1764156373,
    summary: {
      title: 'Updated Session Title',
      description: 'This session was updated via API'
    },
    metadata: {
      category: 'test',
      priority: 'high'
    }
  },
  {
    session_id: 'cf7ad674-6a37-4805-9417-daa9a265471a',
    created_at: 1764150336,
    updated_at: 1764150392,
    summary: {
      title: 'Python Tutorial'
    },
    metadata: null
  },
  {
    session_id: '490c79d1-c274-4130-951c-677b5ea04d8f',
    created_at: 1764150219,
    updated_at: 1764150268,
    summary: {
      title: 'ML Discussion'
    },
    metadata: null
  },
  {
    session_id: 'cc5c94d4-2f62-4459-bf33-d53b6f52e11a',
    created_at: 1764150143,
    updated_at: 1764150171,
    summary: {
      title: 'Python Discussion'
    },
    metadata: null
  }
];

export const MOCK_SESSIONS_RESPONSE: SessionsResponse = {
  sessions: MOCK_SESSIONS,
  total: MOCK_SESSIONS.length
};

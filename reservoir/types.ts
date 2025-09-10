export enum SourceType {
  REDDIT = 'REDDIT'
}

export enum EventType {
  DATA_PRODUCED = 'data.produced'
}

export enum RedditType {
  SUBMISSION = 'submission',
  COMMENT = 'comment'
}

export interface EventMetaData {
  correlation_id: string;
  source_type: SourceType;
  source_date: string;
  event_type: EventType;
}

export interface RedditData {
  id: string;
  reddit_type: RedditType;
  subreddit: string;
  body: string;
}

export interface DataProducedEvent {
  meta: EventMetaData;
  data: any;
}


export interface RedditDataProducedEvent extends DataProducedEvent {
  data: RedditData
}
export const validateRedditDataProducedEvent = (obj: any): obj is RedditDataProducedEvent => {
  if (!obj || typeof obj !== 'object') {
    return false;
  }

  // Validate meta structure
  if (!obj.meta || typeof obj.meta !== 'object') {
    return false;
  }

  const meta = obj.meta;
  
  // Validate meta fields
  if (typeof meta.correlation_id !== 'string' ||
      !Object.values(SourceType).includes(meta.source_type) ||
      typeof meta.source_date !== 'string' ||
      !Object.values(EventType).includes(meta.event_type)) {
    return false;
  }

  // Validate data structure for Reddit
  if (!obj.data || typeof obj.data !== 'object') {
    return false;
  }

  const data = obj.data;

  // Validate Reddit data fields
  if (typeof data.id !== 'string' ||
      !Object.values(RedditType).includes(data.reddit_type) ||
      typeof data.subreddit !== 'string' ||
      typeof data.body !== 'string') {
    return false;
  }

  return true;
}

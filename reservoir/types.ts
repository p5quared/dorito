export enum SourceType {
  REDDIT = 'REDDIT'
}

enum EventType {
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


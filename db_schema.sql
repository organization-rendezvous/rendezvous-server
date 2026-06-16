create table if not exists analysis_jobs (
  id text primary key,
  user_id text not null,
  status text not null,
  period text not null,
  result_limit integer not null,
  sources text[] not null default '{}',
  started_at timestamptz not null,
  completed_at timestamptz,
  error_message text,
  created_at timestamptz not null default now()
);

create table if not exists analysis_topics (
  id text primary key,
  job_id text not null references analysis_jobs(id) on delete cascade,
  topic_name text not null,
  status text not null,
  current_step text,
  document_count integer not null default 0,
  trend_count integer not null default 0,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists trends (
  id text primary key,
  topic_id text not null references analysis_topics(id) on delete cascade,
  title text not null,
  normalized_title text not null,
  rank integer not null,
  final_score numeric not null,
  summary text not null,
  detail_summary text not null,
  ai_comment text not null,
  keywords text[] not null default '{}',
  trend_date date not null,
  period text not null,
  created_at timestamptz not null default now()
);

create table if not exists trend_scores (
  id bigserial primary key,
  trend_id text not null references trends(id) on delete cascade,
  mention_score numeric not null,
  growth_score numeric not null default 0,
  diversity_score numeric not null,
  influence_score numeric not null,
  recency_score numeric not null,
  ai_importance_score numeric not null,
  final_score numeric not null,
  created_at timestamptz not null default now()
);

create table if not exists trend_links (
  id bigserial primary key,
  trend_id text not null references trends(id) on delete cascade,
  title text not null,
  url text not null,
  source_name text not null,
  source_type text not null,
  author text,
  published_at timestamptz,
  summary text,
  relevance_score numeric,
  credibility_score numeric,
  created_at timestamptz not null default now()
);

create table if not exists user_settings (
  id bigserial primary key,
  user_id text not null unique,
  enabled_topics text[] not null default '{}',
  custom_topics text[] not null default '{}',
  period text not null default '24h',
  result_limit integer not null default 5,
  enabled_sources text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_analysis_jobs_user_id on analysis_jobs(user_id);
create index if not exists idx_analysis_jobs_created_at on analysis_jobs(created_at desc);
create index if not exists idx_analysis_topics_job_id on analysis_topics(job_id);
create index if not exists idx_trends_topic_id on trends(topic_id);
create index if not exists idx_trends_rank on trends(rank);
create index if not exists idx_trend_links_trend_id on trend_links(trend_id);

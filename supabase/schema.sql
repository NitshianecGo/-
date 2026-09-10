-- NovaChat 2.0 / Supabase SQL
-- Run this once in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 32),
  avatar text,
  online boolean not null default false,
  last_seen timestamptz default now(),
  created_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id text not null,
  sender_id uuid not null references public.profiles(id) on delete cascade,
  receiver_id uuid not null references public.profiles(id) on delete cascade,
  body text not null default '',
  type text not null default 'text' check (type in ('text','file','voice')),
  file_url text,
  file_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.reactions (
  id uuid primary key default gen_random_uuid(),
  message_id uuid not null references public.messages(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  emoji text not null,
  created_at timestamptz not null default now(),
  unique(message_id,user_id,emoji)
);

alter table public.profiles enable row level security;
alter table public.messages enable row level security;
alter table public.reactions enable row level security;

create policy "profiles readable by authenticated users" on public.profiles for select to authenticated using (true);
create policy "users can create their profile" on public.profiles for insert to authenticated with check (auth.uid()=id);
create policy "users can update own profile" on public.profiles for update to authenticated using (auth.uid()=id) with check (auth.uid()=id);

create policy "messages readable by participants" on public.messages for select to authenticated
using (auth.uid()=sender_id or auth.uid()=receiver_id);
create policy "messages insert by sender" on public.messages for insert to authenticated
with check (auth.uid()=sender_id);

create policy "reactions readable" on public.reactions for select to authenticated using (true);
create policy "users add own reactions" on public.reactions for insert to authenticated with check (auth.uid()=user_id);
create policy "users delete own reactions" on public.reactions for delete to authenticated using (auth.uid()=user_id);

-- Realtime
alter publication supabase_realtime add table public.messages;
alter publication supabase_realtime add table public.reactions;

-- Storage bucket for files/voice.
insert into storage.buckets (id,name,public) values ('chat-files','chat-files',true)
on conflict (id) do update set public=true;

create policy "authenticated can upload chat files"
on storage.objects for insert to authenticated
with check (bucket_id='chat-files' and (storage.foldername(name))[1]=auth.uid()::text);

create policy "public can read chat files"
on storage.objects for select to public
using (bucket_id='chat-files');

-- Anonymous auth must be enabled in Supabase Dashboard:
-- Authentication -> Providers -> Anonymous Sign-Ins -> Enable.

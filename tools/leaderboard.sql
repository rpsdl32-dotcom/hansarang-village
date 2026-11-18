-- 한사랑 마을 · 주간 랭킹 표
-- Supabase 대시보드 → SQL Editor → New query → 이 내용 전체 붙여넣기 → Run (한 번만 하면 됩니다).
-- 점수는 아래 함수로만 들어가고(직접 쓰기 막힘), 누구나 읽을 수 있습니다. 주(週)는 한국 시간 월요일에 바뀝니다.
-- 이상한 닉네임이나 점수는 Table Editor에서 그 줄의 hidden 을 true 로 바꾸면 순위에서 사라집니다.

create table if not exists public.hsv_scores (
  game text not null check (game in ('pk', 'star', 'quiz')),
  week text not null,
  pid text not null check (pid ~ '^[a-z0-9]{8,16}$'),
  nick text not null check (char_length(nick) between 1 and 8),
  score numeric not null,
  updated_at timestamptz not null default now(),
  hidden boolean not null default false,
  primary key (game, week, pid)
);

alter table public.hsv_scores enable row level security;
drop policy if exists hsv_scores_read on public.hsv_scores;
create policy hsv_scores_read on public.hsv_scores for select to anon, authenticated using (not hidden);
revoke insert, update, delete on public.hsv_scores from anon, authenticated;
grant select on public.hsv_scores to anon, authenticated;

create or replace function public.hsv_submit_score(p_game text, p_pid text, p_nick text, p_score numeric)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  w text := to_char(now() at time zone 'Asia/Seoul', 'IYYY-"W"IW');
  cur public.hsv_scores%rowtype;
  better boolean;
begin
  if p_game not in ('pk', 'star', 'quiz') then return 'bad_game'; end if;
  if p_pid is null or p_pid !~ '^[a-z0-9]{8,16}$' then return 'bad_pid'; end if;
  p_nick := left(btrim(coalesce(p_nick, '')), 8);
  if p_nick = '' then p_nick := '손님'; end if;
  if p_score is null then return 'bad_score'; end if;
  if p_game = 'pk'   and (p_score < 0 or p_score > 20  or p_score <> trunc(p_score)) then return 'bad_score'; end if;
  if p_game = 'star' and (p_score < 5 or p_score > 900) then return 'bad_score'; end if;
  if p_game = 'quiz' and (p_score < 0 or p_score > 50  or p_score <> trunc(p_score)) then return 'bad_score'; end if;

  select * into cur from public.hsv_scores where game = p_game and week = w and pid = p_pid;
  if found then
    if cur.updated_at > now() - interval '5 seconds' then return 'slow_down'; end if;
    better := case when p_game = 'star' then p_score < cur.score else p_score > cur.score end;
    if better then
      update public.hsv_scores set score = p_score, nick = p_nick, updated_at = now() where game = p_game and week = w and pid = p_pid;
      return 'best';
    end if;
    update public.hsv_scores set nick = p_nick where game = p_game and week = w and pid = p_pid;
    return 'kept';
  end if;
  insert into public.hsv_scores (game, week, pid, nick, score) values (p_game, w, p_pid, p_nick, p_score);
  return 'best';
end;
$$;

revoke all on function public.hsv_submit_score(text, text, text, numeric) from public;
grant execute on function public.hsv_submit_score(text, text, text, numeric) to anon, authenticated;

-- 확인: 아래 줄을 실행해서 'best' 가 나오면 성공입니다. (시험 점수는 바로 지워집니다)
select public.hsv_submit_score('quiz', 'testsetup01', '설정확인', 1);
delete from public.hsv_scores where pid = 'testsetup01';

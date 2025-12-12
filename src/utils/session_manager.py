import os
import json
import time
from datetime import datetime

class SessionManager:
    def __init__(self, app_state, user_data_path):
        self.app_state = app_state
        self.user_data_path = user_data_path
        self.ui_callback = None
        self.countdown_seconds = 300
        self._block_after_id = None
        self._countdown_after_id = None
        self._countdown_start = None
        self._load_user_data()

    def set_ui_callback(self, cb):
        self.ui_callback = cb

    def _load_user_data(self):
        try:
            if os.path.exists(self.user_data_path):
                with open(self.user_data_path, 'r') as f:
                    self.user_data = json.load(f)
            else:
                self.user_data = {}
        except Exception:
            self.user_data = {}
        if 'study_time' not in self.user_data:
            self.user_data['study_time'] = 0
        if 'sessions' not in self.user_data:
            self.user_data['sessions'] = []

    def _save_user_data(self):
        os.makedirs(os.path.dirname(self.user_data_path), exist_ok=True)
        try:
            with open(self.user_data_path, 'w') as f:
                json.dump(self.user_data, f, indent=2)
        except Exception:
            pass

    def start_session(self):
        if not self.app_state.study_session.get('schedule'):
            return False
        s = self.app_state.study_session
        s['active'] = True
        s['start_time'] = time.time()
        s['last_activity'] = s['start_time']
        s['current_block'] = 0
        s['completed_blocks'] = []
        s['total_study_time'] = 0
        s['session_paused'] = False
        self._start_block()
        return True

    def _start_block(self):
        s = self.app_state.study_session
        if s['current_block'] >= len(s['schedule']['blocks']):
            self._complete_session()
            return
        block = s['schedule']['blocks'][s['current_block']]
        s['block_start_time'] = time.time()
        s['block_type'] = block['type']
        s['block_duration'] = int(block['duration']) * 60
        self._cancel_after(self._countdown_after_id)
        self._countdown_after_id = None
        self._schedule_block_tick()
        if self.ui_callback:
            t = "Study" if block['type'] == 'study' else "Break"
            status = f"Current: {t} Block\nDuration: {block['duration']} minutes\nBlock {s['current_block']+1} of {len(s['schedule']['blocks'])}"
            self.ui_callback(status, show_continue=False)

    def _schedule_block_tick(self):
        self._cancel_after(self._block_after_id)
        self._block_after_id = self.app_state.root.after(1000, self._update_block)

    def _update_block(self):
        s = self.app_state.study_session
        if not s.get('active') or s.get('session_paused'):
            self._schedule_block_tick()
            return
        elapsed = int(time.time() - s.get('block_start_time', time.time()))
        remaining = max(0, int(s.get('block_duration', 0)) - elapsed)
        if remaining <= 0:
            self.complete_block()
            return
        mins, secs = divmod(remaining, 60)
        t = "Study" if s.get('block_type') == 'study' else "Break"
        if self.ui_callback:
            self.ui_callback(f"{t}: {mins:02d}:{secs:02d} remaining", show_continue=False)
        self._schedule_block_tick()

    def complete_block(self):
        s = self.app_state.study_session
        self._cancel_after(self._block_after_id)
        self._block_after_id = None
        if s['current_block'] >= len(s['schedule']['blocks']):
            self._complete_session()
            return False
        block = s['schedule']['blocks'][s['current_block']]
        duration_sec = int(time.time() - s.get('block_start_time', time.time()))
        if block['type'] == 'study':
            self.user_data['study_time'] = int(self.user_data.get('study_time', 0)) + max(0, duration_sec)
            s['total_study_time'] = int(s.get('total_study_time', 0)) + max(0, duration_sec)
        s['completed_blocks'].append({
            'type': block['type'],
            'scheduled_duration': block['duration'],
            'actual_duration_sec': duration_sec,
            'completed_at': datetime.now().isoformat()
        })
        s['current_block'] += 1
        self._start_countdown()
        return True

    def _start_countdown(self):
        s = self.app_state.study_session
        if s['current_block'] >= len(s['schedule']['blocks']):
            self._complete_session()
            return
        self._countdown_start = time.time()
        self._schedule_countdown_tick()

    def _schedule_countdown_tick(self):
        self._cancel_after(self._countdown_after_id)
        self._countdown_after_id = self.app_state.root.after(1000, self._update_countdown)

    def _update_countdown(self):
        s = self.app_state.study_session
        if not s.get('active'):
            return
        elapsed = int(time.time() - (self._countdown_start or time.time()))
        remaining = max(0, self.countdown_seconds - elapsed)
        next_block = s['schedule']['blocks'][s['current_block']]
        t = "Study" if next_block['type'] == 'study' else "Break"
        if remaining <= 0:
            self.end_session()
            return
        mins, secs = divmod(remaining, 60)
        if self.ui_callback:
            self.ui_callback(f"Next {t} block in: {mins:02d}:{secs:02d}\nDuration: {next_block['duration']} minutes", show_continue=True)
        self._schedule_countdown_tick()

    def confirm_next_block(self):
        self._cancel_after(self._countdown_after_id)
        self._countdown_after_id = None
        s = self.app_state.study_session
        if s['current_block'] >= len(s['schedule']['blocks']):
            self._complete_session()
            return False
        self._start_block()
        return True

    def end_session(self):
        return self._complete_session()

    def _complete_session(self):
        s = self.app_state.study_session
        self._cancel_after(self._block_after_id)
        self._cancel_after(self._countdown_after_id)
        self._block_after_id = None
        self._countdown_after_id = None
        if s.get('active'):
            study_time_sec = int(s.get('total_study_time', 0))
            session_data = {
                'start_time': datetime.fromtimestamp(s.get('start_time') or time.time()).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_study_time_sec': study_time_sec,
                'blocks_completed': len(s.get('completed_blocks', [])),
                'schedule_name': (s.get('schedule') or {}).get('name', 'Custom')
            }
            self.user_data['sessions'].append(session_data)
            self._save_user_data()
        s.update({
            'active': False,
            'type': None,
            'schedule': None,
            'current_block': 0,
            'block_type': None,
            'block_duration': 0,
            'block_start_time': None,
            'start_time': None,
            'paused': False,
            'last_activity': None,
            'completed_blocks': [],
            'total_study_time': 0,
            'session_paused': False
        })
        if self.ui_callback:
            self.ui_callback("Session completed!", show_continue=False)
        return max(0, (self.user_data.get('study_time', 0) or 0) // 60)

    def pause(self):
        s = self.app_state.study_session
        if not s.get('active') or s.get('session_paused'):
            return False
        s['session_paused'] = True
        s['pause_time'] = time.time()
        return True

    def resume(self):
        s = self.app_state.study_session
        if not s.get('active') or not s.get('session_paused'):
            return False
        paused_dur = time.time() - s.get('pause_time', time.time())
        if s.get('block_start_time'):
            s['block_start_time'] += paused_dur
        s['session_paused'] = False
        s.pop('pause_time', None)
        return True

    def _cancel_after(self, after_id):
        try:
            if after_id is not None:
                self.app_state.root.after_cancel(after_id)
        except Exception:
            pass

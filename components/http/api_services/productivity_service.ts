/**
 * Productivity API Services
 *
 * Services for Notes, Ideas, and Calendar operations.
 * Built on BaseResourceService with domain-specific extensions.
 */

import {
  ApiClient,
  BaseResourceService,
  query,
} from './base_service';

import type {
  Note,
  NoteListParams,
  CreateNoteRequest,
  UpdateNoteRequest,
  Idea,
  IdeaListParams,
  CreateIdeaRequest,
  UpdateIdeaRequest,
  IdeaStatus,
  CalendarEvent,
  CalendarEventListParams,
  CreateCalendarEventRequest,
  UpdateCalendarEventRequest,
  GoogleCalendarSyncRequest,
  GoogleCalendarSyncResponse,
  ListResponse,
  DeleteResponse,
} from './types';

// ============ NOTES SERVICE ============

/**
 * Notes API service with CRUD operations and specialized methods
 */
export class NotesService extends BaseResourceService<
  Note,
  CreateNoteRequest,
  UpdateNoteRequest,
  NoteListParams,
  ListResponse<Note>
> {
  constructor(client: ApiClient) {
    super(client, { endpoint: '/api/v1/notes' });
  }

  /**
   * Toggle pin status on a note
   */
  async togglePin(id: number): Promise<Note> {
    return this.action<Note>(id, 'pin', 'POST');
  }

  /**
   * Toggle archive status on a note
   */
  async toggleArchive(id: number): Promise<Note> {
    return this.action<Note>(id, 'archive', 'POST');
  }

  /**
   * Get pinned notes
   */
  async getPinned(params?: Omit<NoteListParams, 'is_pinned'>): Promise<ListResponse<Note>> {
    return this.list({ ...params, is_pinned: true });
  }

  /**
   * Get archived notes
   */
  async getArchived(params?: Omit<NoteListParams, 'is_archived'>): Promise<ListResponse<Note>> {
    return this.list({ ...params, is_archived: true });
  }

  /**
   * Get notes by tag
   */
  async getByTag(tag: string, params?: Omit<NoteListParams, 'tag'>): Promise<ListResponse<Note>> {
    return this.list({ ...params, tag });
  }

  /**
   * Get notes for a project
   */
  async getByProject(projectId: number, params?: Omit<NoteListParams, 'project_id'>): Promise<ListResponse<Note>> {
    return this.list({ ...params, project_id: projectId });
  }

  /**
   * Search notes by content
   */
  async search(query: string, params?: Omit<NoteListParams, 'search'>): Promise<ListResponse<Note>> {
    return this.list({ ...params, search: query });
  }
}

// ============ IDEAS SERVICE ============

/**
 * Ideas API service with CRUD operations and status management
 */
export class IdeasService extends BaseResourceService<
  Idea,
  CreateIdeaRequest,
  UpdateIdeaRequest,
  IdeaListParams,
  ListResponse<Idea>
> {
  constructor(client: ApiClient) {
    super(client, { endpoint: '/api/v1/ideas' });
  }

  /**
   * Update idea status
   */
  async updateStatus(id: number, status: IdeaStatus): Promise<Idea> {
    return this.client.patch<Idea>(this.actionUrl(id, 'status'), { status });
  }

  /**
   * Get ideas by status
   */
  async getByStatus(status: IdeaStatus, params?: Omit<IdeaListParams, 'status'>): Promise<ListResponse<Idea>> {
    return this.list({ ...params, status });
  }

  /**
   * Get ideas by priority
   */
  async getByPriority(priority: Idea['priority'], params?: Omit<IdeaListParams, 'priority'>): Promise<ListResponse<Idea>> {
    return this.list({ ...params, priority });
  }

  /**
   * Get ideas by tag
   */
  async getByTag(tag: string, params?: Omit<IdeaListParams, 'tag'>): Promise<ListResponse<Idea>> {
    return this.list({ ...params, tag });
  }

  /**
   * Get active (non-archived) ideas
   */
  async getActive(params?: Omit<IdeaListParams, 'exclude_archived'>): Promise<ListResponse<Idea>> {
    return this.list({ ...params, exclude_archived: true });
  }

  /**
   * Get raw ideas (unrefined)
   */
  async getRaw(params?: Omit<IdeaListParams, 'status'>): Promise<ListResponse<Idea>> {
    return this.getByStatus('raw', params);
  }

  /**
   * Get actionable ideas
   */
  async getActionable(params?: Omit<IdeaListParams, 'status'>): Promise<ListResponse<Idea>> {
    return this.getByStatus('actionable', params);
  }

  /**
   * Promote idea to next status
   */
  async promote(id: number): Promise<Idea> {
    const idea = await this.get(id);
    const statusProgression: Record<IdeaStatus, IdeaStatus> = {
      'raw': 'refined',
      'refined': 'actionable',
      'actionable': 'implemented',
      'implemented': 'archived',
      'archived': 'archived',
    };
    const nextStatus = statusProgression[idea.status];
    return this.updateStatus(id, nextStatus);
  }

  /**
   * Archive idea
   */
  async archive(id: number): Promise<Idea> {
    return this.updateStatus(id, 'archived');
  }

  /**
   * Search ideas
   */
  async search(query: string, params?: Omit<IdeaListParams, 'search'>): Promise<ListResponse<Idea>> {
    return this.list({ ...params, search: query });
  }
}

// ============ CALENDAR SERVICE ============

/**
 * Calendar API service with event management and Google Calendar sync
 */
export class CalendarService extends BaseResourceService<
  CalendarEvent,
  CreateCalendarEventRequest,
  UpdateCalendarEventRequest,
  CalendarEventListParams,
  ListResponse<CalendarEvent>
> {
  constructor(client: ApiClient) {
    super(client, { endpoint: '/api/v1/calendar' });
  }

  /**
   * Get events for today
   */
  async getToday(): Promise<ListResponse<CalendarEvent>> {
    return this.client.get<ListResponse<CalendarEvent>>(`${this.endpoint}/today`);
  }

  /**
   * Get events for current week
   */
  async getWeek(): Promise<ListResponse<CalendarEvent>> {
    return this.client.get<ListResponse<CalendarEvent>>(`${this.endpoint}/week`);
  }

  /**
   * Get events in date range
   */
  async getRange(startDate: string, endDate: string): Promise<ListResponse<CalendarEvent>> {
    return this.list({ start_date: startDate, end_date: endDate });
  }

  /**
   * Get events for a project
   */
  async getByProject(projectId: number): Promise<ListResponse<CalendarEvent>> {
    return this.list({ project_id: projectId });
  }

  /**
   * Get events for a specific date
   */
  async getByDate(date: string): Promise<ListResponse<CalendarEvent>> {
    return this.list({ start_date: date, end_date: date });
  }

  /**
   * Get upcoming events (from today onwards)
   */
  async getUpcoming(days = 30): Promise<ListResponse<CalendarEvent>> {
    const today = new Date().toISOString().split('T')[0];
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + days);
    return this.getRange(today, endDate.toISOString().split('T')[0]);
  }

  /**
   * Sync with Google Calendar
   */
  async syncGoogle(params?: GoogleCalendarSyncRequest): Promise<GoogleCalendarSyncResponse> {
    return this.client.post<GoogleCalendarSyncResponse>(
      `${this.endpoint}/sync/google`,
      params || {}
    );
  }

  /**
   * Create a quick event (with defaults)
   */
  async createQuick(
    title: string,
    startTime: string,
    durationMinutes = 60
  ): Promise<CalendarEvent> {
    const start = new Date(startTime);
    const end = new Date(start.getTime() + durationMinutes * 60 * 1000);
    return this.create({
      title,
      start_time: start.toISOString(),
      end_time: end.toISOString(),
    });
  }

  /**
   * Create an all-day event
   */
  async createAllDay(
    title: string,
    date: string,
    description?: string
  ): Promise<CalendarEvent> {
    return this.create({
      title,
      description,
      start_time: `${date}T00:00:00`,
      end_time: `${date}T23:59:59`,
      all_day: true,
    });
  }
}

// ============ PRODUCTIVITY SERVICE FACADE ============

/**
 * Unified productivity service providing access to all sub-services
 */
export class ProductivityService {
  public readonly notes: NotesService;
  public readonly ideas: IdeasService;
  public readonly calendar: CalendarService;

  constructor(client: ApiClient) {
    this.notes = new NotesService(client);
    this.ideas = new IdeasService(client);
    this.calendar = new CalendarService(client);
  }

  /**
   * Get dashboard summary
   */
  async getDashboardSummary(): Promise<{
    notes: { pinned: number; total: number };
    ideas: { raw: number; actionable: number; total: number };
    calendar: { today: number; week: number };
  }> {
    const [
      pinnedNotes,
      allNotes,
      rawIdeas,
      actionableIdeas,
      allIdeas,
      todayEvents,
      weekEvents,
    ] = await Promise.all([
      this.notes.getPinned({ limit: 0 }),
      this.notes.list({ limit: 0 }),
      this.ideas.getRaw({ limit: 0 }),
      this.ideas.getActionable({ limit: 0 }),
      this.ideas.list({ limit: 0 }),
      this.calendar.getToday(),
      this.calendar.getWeek(),
    ]);

    return {
      notes: {
        pinned: pinnedNotes.total,
        total: allNotes.total,
      },
      ideas: {
        raw: rawIdeas.total,
        actionable: actionableIdeas.total,
        total: allIdeas.total,
      },
      calendar: {
        today: todayEvents.total,
        week: weekEvents.total,
      },
    };
  }

  /**
   * Search across all productivity resources
   */
  async searchAll(query: string): Promise<{
    notes: Note[];
    ideas: Idea[];
  }> {
    const [notesResult, ideasResult] = await Promise.all([
      this.notes.search(query),
      this.ideas.search(query),
    ]);

    return {
      notes: notesResult.items,
      ideas: ideasResult.items,
    };
  }
}

// ============ FACTORY FUNCTIONS ============

/**
 * Create a Notes service instance
 */
export function createNotesService(client: ApiClient): NotesService {
  return new NotesService(client);
}

/**
 * Create an Ideas service instance
 */
export function createIdeasService(client: ApiClient): IdeasService {
  return new IdeasService(client);
}

/**
 * Create a Calendar service instance
 */
export function createCalendarService(client: ApiClient): CalendarService {
  return new CalendarService(client);
}

/**
 * Create a unified Productivity service instance
 */
export function createProductivityService(client: ApiClient): ProductivityService {
  return new ProductivityService(client);
}

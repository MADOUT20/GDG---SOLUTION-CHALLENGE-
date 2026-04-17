insert into baseline (coverage, communities_reached, critical_areas_served, resource_waste)
values (11, 500, 30, 45);

insert into benefits (title, description) values
  ('Targeted allocation', 'Move teams and supplies using actual district-level need instead of assumptions.'),
  ('Faster response', 'Fresh reports and donations update the same operating picture used by coordinators.'),
  ('Measurable planning', 'Coverage, gaps, and recent actions stay visible for every region in one place.');

insert into sources (name, description, records, created_at) values
  ('Paper Surveys', 'Field worker paper forms digitized into the shared hub.', 452, '2026-04-17T08:20'),
  ('Excel Sheets', 'Legacy spreadsheets consolidated from partner NGOs.', 328, '2026-04-17T08:20'),
  ('Mobile App Data', 'Volunteer check-ins collected from mobile outreach visits.', 215, '2026-04-17T08:20'),
  ('Health Center Reports', 'Clinic and community health updates from district partners.', 189, '2026-04-17T08:20'),
  ('School Data', 'Education and child welfare needs reported by schools.', 267, '2026-04-17T08:20'),
  ('Government Surveys', 'District survey snapshots shared by public agencies.', 156, '2026-04-17T08:20');

insert into regions (name, needs, volunteers, target_volunteers, focus) values
  ('Mumbai', 950, 136, 205, 'Water access, medical support, and dense community outreach.'),
  ('Thane', 890, 110, 188, 'Shelter support, health camp staffing, and flood preparedness.'),
  ('Pune', 780, 95, 150, 'Education continuity, family ration kits, and senior care visits.'),
  ('Nagpur', 620, 65, 100, 'Nutrition kits, adolescent health outreach, and local transport.'),
  ('Nashik', 540, 55, 75, 'Water logistics, anganwadi support, and school meal coverage.'),
  ('Aurangabad', 450, 45, 45, 'Monitor emerging needs and maintain standby volunteer readiness.');

insert into activities (title, detail, type, created_at) values
  ('Team deployed to Mumbai', '16 volunteers assigned. No extra deployment note.', 'deployment', '2026-04-17T01:08'),
  ('District records consolidated', 'Six source streams were merged into one planning interface for coordinators.', 'aggregation', '2026-04-17T08:20'),
  ('Priority heatmap refreshed', 'Mumbai and Thane stayed on top after the latest district review.', 'analysis', '2026-04-17T08:45'),
  ('Volunteer plan reviewed', 'Deployment shortlist prepared for Mumbai, Thane, and Pune first.', 'deployment', '2026-04-17T09:10');

insert into deployments (region, volunteers, note, created_at)
values ('Mumbai', 16, '', '2026-04-17T01:08');

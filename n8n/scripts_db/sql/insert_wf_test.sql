
    INSERT INTO shared_workflow ("workflowId", "projectId", role)
    SELECT 'lmweWvhQpkeI9Qc5', project.id, 'workflow:owner'
    FROM project LIMIT 1;
    

    INSERT INTO shared_workflow ("workflowId", "projectId", role)
    SELECT 'H5hoMVs0tClsvuDs', project.id, 'workflow:owner'
    FROM project LIMIT 1;
    
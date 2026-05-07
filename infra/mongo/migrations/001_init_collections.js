let databaseName = db.getName();

if (typeof process !== "undefined" && process.env.MONGO_INITDB_DATABASE) {
  databaseName = process.env.MONGO_INITDB_DATABASE;
}

if (typeof process !== "undefined" && process.env.MONGO_DATABASE) {
  databaseName = process.env.MONGO_DATABASE;
}

const database = db.getSiblingDB(databaseName);

const documentStatuses = [
  "UPLOADED",
  "PROCESSING",
  "COMPLIANT",
  "NON_COMPLIANT",
  "FAILED",
];

function ensureCollection(collectionName, options) {
  const existingCollections = database.getCollectionNames();

  if (!existingCollections.includes(collectionName)) {
    database.createCollection(collectionName, options);
    return;
  }

  database.runCommand({
    collMod: collectionName,
    validator: options.validator,
    validationLevel: options.validationLevel,
    validationAction: options.validationAction,
  });
}

ensureCollection("audit_logs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["action", "entity_type", "entity_id", "created_at"],
      properties: {
        action: {
          bsonType: "string",
        },
        entity_type: {
          bsonType: "string",
        },
        entity_id: {
          bsonType: "string",
          description: "UUID string for the affected entity.",
        },
        user_id: {
          bsonType: ["string", "null"],
          description: "Optional UUID string for the actor.",
        },
        metadata: {
          bsonType: ["object", "null"],
        },
        created_at: {
          bsonType: "date",
        },
      },
    },
  },
  validationLevel: "moderate",
  validationAction: "error",
});

ensureCollection("processing_events", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["document_id", "status", "message", "created_at"],
      properties: {
        document_id: {
          bsonType: "string",
          description: "UUID string for the related document.",
        },
        check_id: {
          bsonType: ["string", "null"],
          description: "Optional UUID string from the compliance check.",
        },
        status: {
          enum: documentStatuses,
        },
        message: {
          bsonType: "string",
        },
        metadata: {
          bsonType: ["object", "null"],
        },
        created_at: {
          bsonType: "date",
        },
      },
    },
  },
  validationLevel: "moderate",
  validationAction: "error",
});

database.getCollection("audit_logs").createIndex(
  { created_at: -1 },
  { name: "idx_audit_logs_created_at" }
);
database.getCollection("audit_logs").createIndex(
  { entity_type: 1, entity_id: 1, created_at: -1 },
  { name: "idx_audit_logs_entity_created_at" }
);
database.getCollection("audit_logs").createIndex(
  { action: 1, created_at: -1 },
  { name: "idx_audit_logs_action_created_at" }
);

database.getCollection("processing_events").createIndex(
  { document_id: 1, created_at: -1 },
  { name: "idx_processing_events_document_created_at" }
);
database.getCollection("processing_events").createIndex(
  { status: 1, created_at: -1 },
  { name: "idx_processing_events_status_created_at" }
);
database.getCollection("processing_events").createIndex(
  { created_at: -1 },
  { name: "idx_processing_events_created_at" }
);

print(`Initialized MongoDB collections in database: ${database.getName()}`);

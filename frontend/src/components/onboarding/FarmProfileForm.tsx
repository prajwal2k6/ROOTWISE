"use client";

import type { FarmData } from "@/types/farm";

type FarmProfileFormProps = {
  farm: FarmData;
  updateFarm: <K extends keyof FarmData>(key: K, value: FarmData[K]) => void;
  onRestoreSample: () => void;
  onSaveFarm: () => void;
  farmSaving: boolean;
};

export default function FarmProfileForm({
  farm,
  updateFarm,
  onRestoreSample,
  onSaveFarm,
  farmSaving,
}: FarmProfileFormProps) {
  return (
    <>
      <div className="rw-step-label">Step 03 of 03 · Farm profile</div>
      <h2>Tell us about your farm.</h2>
      <p>
        Add a few details so ROOTWISE can organise the right environmental indicators and
        compare crop rotations. You can edit these sample values.
      </p>
      <div className="rw-sample-note">
        Sample data is prefilled. Replace it with your farm&apos;s actual details.
      </div>
      <div className="rw-form-grid">
        <Field
          label="Farm name"
          value={farm.farmName}
          onChange={(v) => updateFarm("farmName", v)}
        />
        <Field
          label="Farm size (acres)"
          value={farm.acres}
          onChange={(v) => updateFarm("acres", v)}
          type="number"
        />
        <SelectField
          label="Soil type"
          value={farm.soil}
          onChange={(v) => updateFarm("soil", v)}
          options={[
            "Red loamy soil",
            "Black cotton soil",
            "Sandy soil",
            "Clay soil",
            "Alluvial soil",
            "Not sure",
          ]}
        />
        <SelectField
          label="Irrigation access"
          value={farm.irrigation}
          onChange={(v) => updateFarm("irrigation", v)}
          options={[
            "Borewell",
            "Rain-fed",
            "Canal / river",
            "Drip irrigation",
            "Multiple sources",
            "Not sure",
          ]}
        />
        <Field
          label="Main crop grown"
          value={farm.mainCrop}
          onChange={(v) => updateFarm("mainCrop", v)}
        />
        <Field
          label="Other crops grown"
          value={farm.otherCrops}
          onChange={(v) => updateFarm("otherCrops", v)}
        />
        <SelectField
          label="Usual sowing season / month"
          value={farm.sowing}
          onChange={(v) => updateFarm("sowing", v)}
          options={[
            "Kharif (June–July)",
            "Rabi (October–November)",
            "Summer (February–March)",
            "Multiple seasons",
            "Varies each year",
            "Not sure",
          ]}
        />
        <SelectField
          label="Typical harvest period"
          value={farm.harvest}
          onChange={(v) => updateFarm("harvest", v)}
          options={[
            "September–October",
            "November–December",
            "January–March",
            "April–May",
            "Different times each year",
            "Not sure",
          ]}
        />
        <Field
          label="Previous crop sequence"
          value={farm.sequence}
          onChange={(v) => updateFarm("sequence", v)}
        />
        <SelectField
          label="How often do you grow crops?"
          value={farm.frequency}
          onChange={(v) => updateFarm("frequency", v)}
          options={[
            "Once a year",
            "Twice a year",
            "Three or more times a year",
            "Depends on rainfall and water",
            "Not sure",
          ]}
        />
      </div>
      <label className="rw-label">What would you most like help with?</label>
      <SelectField
        label=""
        value={farm.priority}
        onChange={(v) => updateFarm("priority", v)}
        options={[
          "Save water and manage dry periods",
          "Improve soil health",
          "Improve climate resilience",
          "Balance multiple priorities",
          "Improve crop productivity",
          "Not sure",
        ]}
      />
      <label className="rw-label">Previous crops grown (optional)</label>
      <textarea
        className="rw-field"
        rows={2}
        value={farm.notes}
        onChange={(event) => updateFarm("notes", event.target.value)}
        placeholder="e.g. Ragi → Groundnut → Maize"
      />
      <div className="rw-form-actions">
        <button className="rw-secondary" onClick={onRestoreSample}>
          ↻ Restore sample data
        </button>
        <button className="rw-submit" onClick={onSaveFarm} disabled={farmSaving}>
          {farmSaving ? "Saving farm..." : "Save farm details →"}
        </button>
      </div>
      <p className="rw-helper">
        Sample values are fictional examples for testing. Replace them with accurate farm
        information before using real analysis.
      </p>
    </>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <div>
      <label className="rw-label">{label}</label>
      <input
        className="rw-field"
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div>
      {label && <label className="rw-label">{label}</label>}
      <select
        className="rw-field"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </div>
  );
}

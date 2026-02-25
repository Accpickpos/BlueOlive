'use client';

import { ArrowRight, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';

interface AnalysisResult {
  headers: string[];
  total_rows: number;
  sample_rows: string[][];
  suggested_mappings: Record<string, string>;
  available_model_fields: string[];
  delimiter: string;
  model_type: string;
}

interface FieldMapperProps {
  analysis: AnalysisResult | null;
  mappings: Record<string, string>;
  onMappingsChange: (mappings: Record<string, string>) => void;
  fieldLabels: Record<string, string>;
  requiredField: string;
}

export function FieldMapper({ 
  analysis, 
  mappings, 
  onMappingsChange, 
  fieldLabels,
  requiredField 
}: FieldMapperProps) {
  if (!analysis) return null;

  const availableFields = analysis.available_model_fields || Object.keys(fieldLabels);
  const suggestedMappings = analysis.suggested_mappings || {};

  const handleMappingChange = (header: string, modelField: string) => {
    onMappingsChange({
      ...mappings,
      [header]: modelField,
    });
  };

  const isRequiredMapped = Object.values(mappings).includes(requiredField);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Map Fields</h2>
        <p className="text-gray-600 text-sm">
          Match your CSV columns to the {analysis.model_type} fields
        </p>
      </div>

      {/* Analysis summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-blue-600" />
          <span className="text-blue-800">
            Found {analysis.total_rows} rows with {analysis.headers.length} columns
            (Delimiter: {analysis.delimiter === ',' ? 'comma' : analysis.delimiter === '\t' ? 'tab' : analysis.delimiter})
          </span>
        </div>
      </div>

      {/* Required field warning */}
      {!isRequiredMapped && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span className="text-red-800">
              Warning: Required field "{fieldLabels[requiredField] || requiredField}" is not mapped
            </span>
          </div>
        </div>
      )}

      {/* Sample data preview */}
      {analysis.sample_rows && analysis.sample_rows.length > 0 && (
        <div className="overflow-x-auto border rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {analysis.headers.map((header, idx) => (
                  <th key={idx} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analysis.sample_rows.slice(0, 3).map((row, rowIdx) => (
                <tr key={rowIdx}>
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                      {cell || '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Field mapping */}
      <div className="space-y-3">
        <h3 className="font-medium text-gray-900">Column Mappings</h3>
        {analysis.headers.map((header) => (
          <div key={header} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex-1 min-w-0">
              <span className="text-sm font-medium text-gray-900">{header}</span>
            </div>
            
            <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
            
            <select
              value={mappings[header] || ''}
              onChange={(e) => handleMappingChange(header, e.target.value)}
              className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">-- Skip this column --</option>
              {availableFields.map((field) => (
                <option 
                  key={field} 
                  value={field}
                  className={field === requiredField ? 'font-bold' : ''}
                >
                  {fieldLabels[field] || field} {field === requiredField ? ' *' : ''}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>

      {/* Suggested mappings info */}
      {Object.keys(suggestedMappings).length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span className="font-medium text-green-800">Auto-detected mappings:</span>
          </div>
          <div className="text-sm text-green-700 space-y-1">
            {Object.entries(suggestedMappings).map(([csvField, modelField]) => (
              <p key={csvField}>
                {csvField} → {fieldLabels[modelField as string] || modelField}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
